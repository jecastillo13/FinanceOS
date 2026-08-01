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
        Transferencia,
        Presupuesto,
        Meta,
        MetaOperacion,
        Inversion,
        Configuracion,
        Auditoria,
        TasaCambio,
    )

    Base.metadata.create_all(bind=engine)
    _ejecutar_migraciones()


def _migrar_categoria(conexion):
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
    for nombre, definicion in campos.items():
        if nombre not in columnas:
            conexion.execute(text(f"ALTER TABLE categorias ADD COLUMN {nombre} {definicion}"))


def _crear_indices_operativos(conexion):
    """Crea indices compatibles con instalaciones existentes de SQLite."""
    indices = (
        "CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos(fecha)",
        "CREATE INDEX IF NOT EXISTS idx_movimientos_cuenta_fecha ON movimientos(cuenta_id, fecha)",
        "CREATE INDEX IF NOT EXISTS idx_movimientos_categoria_fecha ON movimientos(categoria_id, fecha)",
        "CREATE INDEX IF NOT EXISTS idx_auditoria_fecha ON auditoria(fecha)",
        "CREATE INDEX IF NOT EXISTS idx_tasas_par ON tasas_cambio(moneda_origen, moneda_destino)",
        "CREATE INDEX IF NOT EXISTS idx_presupuestos_periodo ON presupuestos(anio, mes, categoria_id)",
        "CREATE INDEX IF NOT EXISTS idx_meta_operaciones_meta_fecha ON meta_operaciones(meta_id, fecha)",
    )
    for sentencia in indices:
        conexion.execute(text(sentencia))


def _migrar_metas(conexion):
    """Amplia metas existentes sin eliminar los objetivos ya creados."""
    columnas = {columna["name"] for columna in inspect(engine).get_columns("metas")}
    campos = {
        "descripcion": "TEXT DEFAULT ''",
        "moneda": "VARCHAR(10) NOT NULL DEFAULT 'COP'",
        "activa": "INTEGER NOT NULL DEFAULT 1",
    }
    for nombre, definicion in campos.items():
        if nombre not in columnas:
            conexion.execute(text(f"ALTER TABLE metas ADD COLUMN {nombre} {definicion}"))


def _ejecutar_migraciones():
    """Aplica migraciones idempotentes y registra la version local."""
    migraciones = (
        ("001_categoria_enriquecida", _migrar_categoria),
        ("002_indices_operativos", _crear_indices_operativos),
        ("003_metas_inteligentes", _migrar_metas),
    )
    with engine.begin() as conexion:
        conexion.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(100) PRIMARY KEY,
                aplicada_en DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """))
        aplicadas = {
            fila[0]
            for fila in conexion.execute(text("SELECT version FROM schema_migrations"))
        }
        for version, migracion in migraciones:
            if version in aplicadas:
                continue
            migracion(conexion)
            conexion.execute(
                text("INSERT INTO schema_migrations (version) VALUES (:version)"),
                {"version": version},
            )
