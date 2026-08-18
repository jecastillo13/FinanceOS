"""Aísla toda la suite de la base personal antes de importar la aplicación."""

import os
import tempfile
from pathlib import Path


_ENTORNO_PRUEBAS = tempfile.TemporaryDirectory(prefix="financeos_pytest_")
os.environ["FINANCEOS_DATABASE_URL"] = f"sqlite:///{(Path(_ENTORNO_PRUEBAS.name) / 'suite.db').as_posix()}"


def pytest_sessionfinish(session, exitstatus):
    del session, exitstatus
    from core.database import engine

    engine.dispose()
    _ENTORNO_PRUEBAS.cleanup()
