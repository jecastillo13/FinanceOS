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

DEFAULT_DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
DATABASE_URL = os.getenv("FINANCEOS_DATABASE_URL", DEFAULT_DATABASE_URL).strip()

# ===========================
# Engine
# ===========================

opciones_engine = {"echo": False}
if DATABASE_URL.startswith("sqlite"):
    opciones_engine["connect_args"] = {"check_same_thread": False}
else:
    opciones_engine["pool_pre_ping"] = True

engine = create_engine(DATABASE_URL, **opciones_engine)

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
        AdjuntoMovimiento,
        GastoRecurrente,
        Transferencia,
        Presupuesto,
        Meta,
        MetaOperacion,
        Inversion,
        Configuracion,
        Auditoria,
        TasaCambio,
        Tarjeta,
        OperacionDetectada,
        Usuario,
        SesionUsuario,
    )

    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "sqlite":
        _ejecutar_migraciones()
    else:
        # PostgreSQL también puede recibir una instalación ya existente. La
        # inspección idempotente evita depender de SQLite al escalar a web.
        with engine.begin() as conexion:
            _migrar_propiedad_por_usuario(conexion)


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
        "CREATE INDEX IF NOT EXISTS idx_tarjetas_ultimos_cuatro ON tarjetas(ultimos_cuatro)",
        "CREATE INDEX IF NOT EXISTS idx_operaciones_detectadas_estado_fecha ON operaciones_detectadas(estado, fecha)",
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


def _migrar_idempotencia_movimientos(conexion):
    """Permite reconocer comprobantes ya importados sin alterar datos previos."""
    columnas = {columna["name"] for columna in inspect(engine).get_columns("movimientos")}
    if "huella" not in columnas:
        conexion.execute(text("ALTER TABLE movimientos ADD COLUMN huella VARCHAR(64)"))
    conexion.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_movimiento_huella ON movimientos(huella)"))


def _migrar_propiedad_por_usuario(conexion):
    """Asigna los datos históricos al primer propietario y prepara el aislamiento."""
    from core.ownership import TABLAS_CON_PROPIETARIO

    columnas_usuario = {columna["name"] for columna in inspect(engine).get_columns("usuarios")}
    if "rol" not in columnas_usuario:
        conexion.execute(text("ALTER TABLE usuarios ADD COLUMN rol VARCHAR(20) NOT NULL DEFAULT 'usuario'"))
    propietario = conexion.execute(text("SELECT id FROM usuarios ORDER BY id LIMIT 1")).scalar()
    if propietario is not None:
        conexion.execute(text("UPDATE usuarios SET rol = 'administrador' WHERE id = :id"), {"id": propietario})

    tablas = set(inspect(engine).get_table_names())
    for tabla in TABLAS_CON_PROPIETARIO:
        if tabla not in tablas:
            continue
        columnas = {columna["name"] for columna in inspect(engine).get_columns(tabla)}
        if "usuario_id" not in columnas:
            conexion.execute(text(f"ALTER TABLE {tabla} ADD COLUMN usuario_id INTEGER"))
        conexion.execute(text(f"CREATE INDEX IF NOT EXISTS idx_{tabla}_usuario ON {tabla}(usuario_id)"))
        if propietario is not None:
            conexion.execute(
                text(f"UPDATE {tabla} SET usuario_id = :usuario_id WHERE usuario_id IS NULL"),
                {"usuario_id": propietario},
            )

    # El índice histórico hacía global la huella. Ahora dos usuarios pueden
    # importar legítimamente el mismo comprobante sin compartir registros.
    conexion.execute(text("DROP INDEX IF EXISTS uq_movimiento_huella"))
    conexion.execute(text(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_movimiento_usuario_huella "
        "ON movimientos(usuario_id, huella)"
    ))


def _ejecutar_migraciones():
    """Aplica migraciones idempotentes y registra la version local."""
    migraciones = (
        ("001_categoria_enriquecida", _migrar_categoria),
        ("002_indices_operativos", _crear_indices_operativos),
        ("003_metas_inteligentes", _migrar_metas),
        ("004_tarjetas_y_detecciones", _crear_indices_operativos),
        ("005_idempotencia_movimientos", _migrar_idempotencia_movimientos),
        ("006_propiedad_por_usuario", _migrar_propiedad_por_usuario),
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
