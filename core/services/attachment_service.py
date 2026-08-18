from pathlib import Path
from uuid import uuid4

from core.database import BASE_DIR, get_session
from core.models import AdjuntoMovimiento, Movimiento
from core.services.audit_service import registrar_auditoria


def eliminar_archivos_adjuntos(movimiento):
    """Elimina del disco los comprobantes que desaparecerán con un movimiento."""
    for adjunto in list(movimiento.adjuntos):
        ruta = Path(BASE_DIR) / adjunto.ruta
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
    FIRMAS_VALIDAS = {
        "image/jpeg": lambda datos: datos.startswith(b"\xff\xd8\xff"),
        "image/png": lambda datos: datos.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/webp": lambda datos: len(datos) >= 12 and datos.startswith(b"RIFF") and datos[8:12] == b"WEBP",
        "application/pdf": lambda datos: datos.startswith(b"%PDF-"),
    }

    def __init__(self):
        self.db = get_session()
        self.carpeta = Path(BASE_DIR) / "uploads" / "movimientos"

    def guardar(self, movimiento_id, nombre, contenido, tipo_mime):
        movimiento = self.db.get(Movimiento, movimiento_id)
        if movimiento is None:
            raise ValueError("El movimiento seleccionado no existe.")
        if tipo_mime not in self.TIPOS_PERMITIDOS:
            raise ValueError("Solo puedes adjuntar imágenes JPG, PNG, WEBP o archivos PDF.")
        if not contenido or len(contenido) > self.TAMANO_MAXIMO:
            raise ValueError("El comprobante debe pesar entre 1 byte y 10 MB.")
        if not self.FIRMAS_VALIDAS[tipo_mime](contenido):
            raise ValueError("El contenido del comprobante no coincide con un archivo válido.")

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
        ruta = Path(BASE_DIR) / adjunto.ruta
        return ruta.read_bytes() if ruta.is_file() else None

    def eliminar(self, adjunto_id):
        adjunto = self.db.get(AdjuntoMovimiento, adjunto_id)
        if adjunto is None:
            return False
        ruta = Path(BASE_DIR) / adjunto.ruta
        if ruta.is_file():
            ruta.unlink()
        registrar_auditoria(self.db, "COMPROBANTE_ELIMINADO", f"Comprobante eliminado: {adjunto.nombre}.")
        self.db.delete(adjunto)
        self.db.commit()
        return True

    def cerrar(self):
        self.db.close()
