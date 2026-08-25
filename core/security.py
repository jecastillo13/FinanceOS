"""Controles antiabuso locales y compartidos por la base de datos."""

from collections import defaultdict, deque
from threading import Lock
from time import monotonic
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError


class LimitadorSolicitudes:
    def __init__(self):
        self._eventos = defaultdict(deque)
        self._lock = Lock()

    def permitir(self, clave: str, maximo: int, ventana_segundos: int):
        ahora = monotonic()
        with self._lock:
            eventos = self._eventos[clave]
            while eventos and eventos[0] <= ahora - ventana_segundos:
                eventos.popleft()
            if len(eventos) >= maximo:
                return False, max(1, int(ventana_segundos - (ahora - eventos[0])))
            eventos.append(ahora)
            return True, 0


limitador = LimitadorSolicitudes()


class LimitadorCompartido:
    """Ventanas persistentes compatibles con SQLite y PostgreSQL."""

    def permitir(self, clave: str, maximo: int, ventana_segundos: int):
        from core.database import get_session
        from core.models import IntentoAcceso

        db = get_session()
        ahora = datetime.now()
        try:
            consulta = db.query(IntentoAcceso).filter(IntentoAcceso.clave == clave)
            if db.bind.dialect.name != "sqlite":
                consulta = consulta.with_for_update()
            registro = consulta.first()
            if registro is None:
                db.add(IntentoAcceso(clave=clave, cantidad=1, ventana_inicio=ahora))
                try:
                    db.commit()
                    return True, 0
                except IntegrityError:
                    # Otro proceso creó la misma ventana simultáneamente.
                    db.rollback()
                    registro = db.query(IntentoAcceso).filter(IntentoAcceso.clave == clave).first()
                    if registro is None:
                        raise
            fin = registro.ventana_inicio + timedelta(seconds=ventana_segundos)
            if ahora >= fin:
                registro.cantidad = 1
                registro.ventana_inicio = ahora
                db.commit()
                return True, 0
            if registro.cantidad >= maximo:
                return False, max(1, int((fin - ahora).total_seconds()))
            registro.cantidad += 1
            db.commit()
            return True, 0
        finally:
            db.close()


limitador_compartido = LimitadorCompartido()
