from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# ===========================
# Rutas
# ===========================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_FOLDER = os.path.join(BASE_DIR, "database")

os.makedirs(DB_FOLDER, exist_ok=True)

DATABASE_PATH = os.path.join(DB_FOLDER, "finance.db")

DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# ===========================
# Engine
# ===========================

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# ===========================
# Obtener sesión
# ===========================

def get_session():
    return SessionLocal()


# ===========================
# Crear Base de Datos
# ===========================

def create_database():

    from core.models import (
        Cuenta,
        Categoria,
        Movimiento,
        GastoRecurrente,
        Meta,
        Inversion,
        Configuracion,
        Auditoria,
        TasaCambio,
    )

    Base.metadata.create_all(bind=engine)
    _migrar_categoria()


def _migrar_categoria():
    """Añade los campos nuevos sin eliminar las categorías existentes."""
    columnas = {columna["name"] for columna in inspect(engine).get_columns("categorias")}
    campos = {
        "icono": "VARCHAR(50) DEFAULT '🏷️'",
        "grupo": "VARCHAR(80) DEFAULT 'Otros'",
        "es_sistema": "INTEGER NOT NULL DEFAULT 0",
        "editable": "INTEGER NOT NULL DEFAULT 1",
        "activa": "INTEGER NOT NULL DEFAULT 1",
        "orden": "INTEGER NOT NULL DEFAULT 0",
    }
    with engine.begin() as conexion:
        for nombre, definicion in campos.items():
            if nombre not in columnas:
                conexion.execute(text(f"ALTER TABLE categorias ADD COLUMN {nombre} {definicion}"))
