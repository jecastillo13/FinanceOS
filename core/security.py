"""Controles de abuso de proceso único; en clúster deben respaldarse con Redis/proxy."""

from collections import defaultdict, deque
from threading import Lock
from time import monotonic


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
