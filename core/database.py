from sqlalchemy import create_engine
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
