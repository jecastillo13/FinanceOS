from pathlib import Path
from uuid import uuid4
from io import BytesIO

from PIL import Image, UnidentifiedImageError
from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError

from core.database import BASE_DIR, get_session
from core.models import AdjuntoMovimiento, Movimiento
from core.services.audit_service import registrar_auditoria


def eliminar_archivos_adjuntos(movimiento):
    """Elimina del disco los comprobantes que desaparecerán con un movimiento."""
    for adjunto in list(movimiento.adjuntos):
        ruta = AttachmentService._ruta_segura(adjunto.ruta)
        if ruta.is_file():
            ruta.unlink()


class AttachmentService:
    """Guarda comprobantes locales vinculados a movimientos financieros."""

    TIPOS_PERMITIDOS = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "application/pdf": ".pdf",
    }
    TAMANO_MAXIMO = 10 * 1024 * 1024
    PIXELES_MAXIMOS = 24_000_000
    PAGINAS_PDF_MAXIMAS = 25
    FIRMAS_VALIDAS = {
        "image/jpeg": lambda datos: datos.startswith(b"\xff\xd8\xff"),
        "image/png": lambda datos: datos.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/webp": lambda datos: len(datos) >= 12 and datos.startswith(b"RIFF") and datos[8:12] == b"WEBP",
        "application/pdf": lambda datos: datos.startswith(b"%PDF-"),
    }

    @classmethod
    def validar_y_sanear(cls, contenido, tipo_mime):
        if tipo_mime not in cls.TIPOS_PERMITIDOS:
            raise ValueError("Solo puedes adjuntar imágenes JPG, PNG, WEBP o archivos PDF.")
        if not contenido or len(contenido) > cls.TAMANO_MAXIMO:
            raise ValueError("El comprobante debe pesar entre 1 byte y 10 MB.")
        if not cls.FIRMAS_VALIDAS[tipo_mime](contenido):
            raise ValueError("El contenido del comprobante no coincide con un archivo válido.")
        if tipo_mime == "application/pdf":
            return cls._validar_pdf(contenido)
        return cls._sanear_imagen(contenido, tipo_mime)

    @classmethod
    def _sanear_imagen(cls, contenido, tipo_mime):
        try:
            with Image.open(BytesIO(contenido)) as imagen:
                ancho, alto = imagen.size
                if ancho <= 0 or alto <= 0 or ancho * alto > cls.PIXELES_MAXIMOS:
                    raise ValueError("La imagen supera el límite seguro de resolución.")
                imagen.verify()
            with Image.open(BytesIO(contenido)) as imagen:
                imagen.load()
                if imagen.mode not in ("RGB", "RGBA", "L"):
                    imagen = imagen.convert("RGB")
                imagen_limpia = Image.frombytes(imagen.mode, imagen.size, imagen.tobytes())
                salida = BytesIO()
                formato = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}[tipo_mime]
                if formato == "JPEG" and imagen_limpia.mode not in ("RGB", "L"):
                    imagen_limpia = imagen_limpia.convert("RGB")
                imagen_limpia.save(salida, format=formato, optimize=True)
                saneada = salida.getvalue()
        except (Image.DecompressionBombError, UnidentifiedImageError, OSError) as error:
            raise ValueError("La imagen está dañada o no puede procesarse de forma segura.") from error
        if len(saneada) > cls.TAMANO_MAXIMO:
            raise ValueError("La imagen procesada supera el límite de 10 MB.")
        return saneada

    @classmethod
    def _validar_pdf(cls, contenido):
        peligrosos = {"/JavaScript", "/JS", "/OpenAction", "/AA", "/Launch", "/EmbeddedFile", "/RichMedia", "/XFA"}
        try:
            lector = PdfReader(BytesIO(contenido), strict=True)
            if lector.is_encrypted:
                raise ValueError("No se permiten comprobantes PDF cifrados.")
            if not lector.pages or len(lector.pages) > cls.PAGINAS_PDF_MAXIMAS:
                raise ValueError("El PDF supera los límites seguros de páginas.")
            pendientes = [lector.trailer]
            visitados = set()
            nodos = 0
            while pendientes:
                objeto = pendientes.pop()
                try:
                    objeto = objeto.get_object()
                except AttributeError:
                    pass
                identidad = id(objeto)
                if identidad in visitados:
                    continue
                visitados.add(identidad)
                nodos += 1
                if nodos > 10_000:
                    raise ValueError("El PDF supera el límite seguro de objetos.")
                if isinstance(objeto, dict):
                    if any(str(clave) in peligrosos for clave in objeto):
                        raise ValueError("El PDF contiene acciones o contenido activo no permitido.")
                    pendientes.extend(objeto.values())
                elif isinstance(objeto, (list, tuple)):
                    pendientes.extend(objeto)
            escritor = PdfWriter()
            for pagina in lector.pages:
                escritor.add_page(pagina)
            escritor.add_metadata({})
            salida = BytesIO()
            escritor.write(salida)
            saneado = salida.getvalue()
        except (PdfReadError, OSError, ValueError) as error:
            if isinstance(error, ValueError):
                raise
            raise ValueError("El PDF está dañado o no puede procesarse de forma segura.") from error
        if len(saneado) > cls.TAMANO_MAXIMO:
            raise ValueError("El PDF procesado supera el límite de 10 MB.")
        return saneado

    def __init__(self):
        self.db = get_session()
        self.carpeta = Path(BASE_DIR) / "uploads" / "movimientos"

    def guardar(self, movimiento_id, nombre, contenido, tipo_mime):
        movimiento = self.db.get(Movimiento, movimiento_id)
        if movimiento is None:
            raise ValueError("El movimiento seleccionado no existe.")
        contenido = self.validar_y_sanear(contenido, tipo_mime)

        # Una repeticion de red o un doble toque no debe crear dos adjuntos.
        for existente in movimiento.adjuntos:
            if existente.tamano != len(contenido):
                continue
            ruta_existente = Path(BASE_DIR) / existente.ruta
            if ruta_existente.is_file() and ruta_existente.read_bytes() == contenido:
                return existente

        self.carpeta.mkdir(parents=True, exist_ok=True)
        extension = self.TIPOS_PERMITIDOS[tipo_mime]
        ruta = self.carpeta / f"{uuid4().hex}{extension}"
        ruta.write_bytes(contenido)
        adjunto = AdjuntoMovimiento(
            movimiento_id=movimiento.id,
            nombre=Path(nombre or f"comprobante{extension}").name[:180],
            ruta=str(ruta.relative_to(BASE_DIR)),
            tipo_mime=tipo_mime,
            tamano=len(contenido),
        )
        self.db.add(adjunto)
        registrar_auditoria(self.db, "COMPROBANTE_ADJUNTADO", f"Comprobante adjuntado al movimiento #{movimiento.id}: {adjunto.nombre}.")
        self.db.commit()
        self.db.refresh(adjunto)
        return adjunto

    def obtener_por_movimiento(self, movimiento_id):
        return (
            self.db.query(AdjuntoMovimiento)
            .filter(AdjuntoMovimiento.movimiento_id == movimiento_id)
            .order_by(AdjuntoMovimiento.fecha.desc())
            .all()
        )

    def obtener(self, adjunto_id):
        return self.db.get(AdjuntoMovimiento, adjunto_id)

    def leer(self, adjunto):
        ruta = self._ruta_segura(adjunto.ruta)
        return ruta.read_bytes() if ruta.is_file() else None

    def eliminar(self, adjunto_id):
        adjunto = self.db.get(AdjuntoMovimiento, adjunto_id)
        if adjunto is None:
            return False
        ruta = self._ruta_segura(adjunto.ruta)
        if ruta.is_file():
            ruta.unlink()
        registrar_auditoria(self.db, "COMPROBANTE_ELIMINADO", f"Comprobante eliminado: {adjunto.nombre}.")
        self.db.delete(adjunto)
        self.db.commit()
        return True

    def cerrar(self):
        self.db.close()

    @staticmethod
    def _ruta_segura(ruta_relativa):
        base = (Path(BASE_DIR) / "uploads").resolve()
        ruta = (Path(BASE_DIR) / ruta_relativa).resolve()
        if not ruta.is_relative_to(base):
            raise ValueError("La ruta del comprobante no es válida.")
        return ruta
