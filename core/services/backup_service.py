import json
import os
import sqlite3
import tempfile
from datetime import datetime
from io import BytesIO
from pathlib import Path, PurePosixPath
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from core.database import BASE_DIR, DATABASE_URL, engine


class BackupService:
    """Crea y restaura respaldos locales sin mantener el archivo en memoria al navegar."""

    TAMANO_MAXIMO = 250 * 1024 * 1024
    TABLAS_REQUERIDAS = {"cuentas", "categorias", "movimientos", "configuracion"}

    @property
    def disponible(self):
        return DATABASE_URL.startswith("sqlite")

    @property
    def database_path(self):
        return Path(engine.url.database).resolve()

    def estado(self):
        ruta = self.database_path
        return {
            "motor": engine.dialect.name,
            "ruta": str(ruta),
            "tamano": ruta.stat().st_size if ruta.is_file() else 0,
            "modificado": datetime.fromtimestamp(ruta.stat().st_mtime) if ruta.is_file() else None,
        }

    def crear_respaldo(self):
        if not self.disponible:
            raise ValueError("Los respaldos locales están disponibles únicamente cuando FinanceOS usa SQLite.")
        origen = self.database_path
        if not origen.is_file():
            raise ValueError("La base de datos local todavía no existe.")

        temporal = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        temporal.close()
        temporal_path = Path(temporal.name)
        try:
            conexion_origen = sqlite3.connect(origen)
            conexion_destino = sqlite3.connect(temporal_path)
            try:
                conexion_origen.backup(conexion_destino)
            finally:
                conexion_destino.close()
                conexion_origen.close()

            salida = BytesIO()
            with ZipFile(salida, "w", ZIP_DEFLATED) as archivo:
                archivo.write(temporal_path, "database/finance.db")
                manifiesto = {
                    "aplicacion": "FinanceOS",
                    "version_respaldo": 1,
                    "creado": datetime.now().isoformat(timespec="seconds"),
                    "motor": "sqlite",
                }
                archivo.writestr("manifest.json", json.dumps(manifiesto, ensure_ascii=False, indent=2))
                uploads = Path(BASE_DIR) / "uploads"
                if uploads.is_dir():
                    for ruta in uploads.rglob("*"):
                        if ruta.is_file():
                            archivo.write(ruta, PurePosixPath("uploads") / ruta.relative_to(uploads))
            return salida.getvalue()
        finally:
            temporal_path.unlink(missing_ok=True)

    def restaurar(self, contenido):
        if not self.disponible:
            raise ValueError("La restauración local está disponible únicamente con SQLite.")
        if not contenido or len(contenido) > self.TAMANO_MAXIMO:
            raise ValueError("El respaldo debe pesar entre 1 byte y 250 MB.")

        try:
            with ZipFile(BytesIO(contenido)) as archivo:
                nombres = archivo.namelist()
                self._validar_rutas(nombres)
                if "database/finance.db" not in nombres:
                    raise ValueError("El ZIP no contiene una base de datos de FinanceOS.")
                datos_db = archivo.read("database/finance.db")
                adjuntos = {
                    nombre: archivo.read(nombre)
                    for nombre in nombres
                    if nombre.startswith("uploads/") and not nombre.endswith("/")
                }
        except BadZipFile as error:
            raise ValueError("El archivo seleccionado no es un respaldo ZIP válido.") from error

        destino = self.database_path
        destino.parent.mkdir(parents=True, exist_ok=True)
        temporal = destino.with_suffix(".restore.tmp")
        temporal.write_bytes(datos_db)
        try:
            self._validar_sqlite(temporal)
            respaldo_seguridad = self._guardar_respaldo_seguridad()
            engine.dispose()
            os.replace(temporal, destino)
            self._restaurar_adjuntos(adjuntos)
            return respaldo_seguridad
        finally:
            temporal.unlink(missing_ok=True)

    @staticmethod
    def _validar_rutas(nombres):
        for nombre in nombres:
            ruta = PurePosixPath(nombre)
            if ruta.is_absolute() or ".." in ruta.parts:
                raise ValueError("El respaldo contiene rutas no permitidas.")

    def _validar_sqlite(self, ruta):
        if ruta.read_bytes()[:16] != b"SQLite format 3\x00":
            raise ValueError("La base incluida no tiene un formato SQLite válido.")
        conexion = None
        try:
            conexion = sqlite3.connect(ruta)
            integridad = conexion.execute("PRAGMA integrity_check").fetchone()[0]
            tablas = {fila[0] for fila in conexion.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        except sqlite3.DatabaseError as error:
            raise ValueError("No fue posible leer la base del respaldo.") from error
        finally:
            if conexion is not None:
                conexion.close()
        if integridad != "ok" or not self.TABLAS_REQUERIDAS.issubset(tablas):
            raise ValueError("El respaldo está incompleto o su base de datos está dañada.")

    def _guardar_respaldo_seguridad(self):
        destino = self.database_path.parent / "backups"
        destino.mkdir(parents=True, exist_ok=True)
        ruta = destino / f"antes_de_restaurar_{datetime.now():%Y%m%d_%H%M%S}.zip"
        ruta.write_bytes(self.crear_respaldo())
        return ruta

    @staticmethod
    def _restaurar_adjuntos(adjuntos):
        base = Path(BASE_DIR)
        for nombre, contenido in adjuntos.items():
            destino = base.joinpath(*PurePosixPath(nombre).parts)
            destino.parent.mkdir(parents=True, exist_ok=True)
            destino.write_bytes(contenido)
