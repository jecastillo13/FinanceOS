from sqlalchemy import Numeric, create_engine, inspect, text
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
        TokenSeguridadUsuario,
        IntentoAcceso,
    )

    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "sqlite":
        _ejecutar_migraciones()
    else:
        # PostgreSQL también puede recibir una instalación ya existente. La
        # inspección idempotente evita depender de SQLite al escalar a web.
        with engine.begin() as conexion:
            _migrar_propiedad_por_usuario(conexion)
            _migrar_roles_publicacion(conexion)
            _migrar_seguridad_cuentas(conexion)
            _migrar_mfa(conexion)
            _migrar_mfa_antireplay(conexion)
            _migrar_sesiones_seguras(conexion)
            _migrar_dinero_decimal(conexion)
            _migrar_inversiones_trazables(conexion)
            _migrar_cuentas_producto(conexion)


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
        conexion.execute(text(
            "UPDATE usuarios SET rol = 'administrador' WHERE id = :id "
            "AND NOT EXISTS (SELECT 1 FROM usuarios WHERE rol IN ('administrador', 'superadmin'))"
        ), {"id": propietario})

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


def _migrar_roles_publicacion(conexion):
    """Convierte el administrador local existente en superadministrador."""
    if "usuarios" not in set(inspect(engine).get_table_names()):
        return
    conexion.execute(text("UPDATE usuarios SET rol = 'superadmin' WHERE rol = 'administrador'"))


def _migrar_seguridad_cuentas(conexion):
    """Añade verificación de correo sin bloquear instalaciones privadas existentes."""
    if "usuarios" not in set(inspect(engine).get_table_names()):
        return
    columnas = {columna["name"] for columna in inspect(engine).get_columns("usuarios")}
    if "correo_verificado_en" not in columnas:
        conexion.execute(text("ALTER TABLE usuarios ADD COLUMN correo_verificado_en DATETIME"))
        # Las cuentas anteriores ya demostraron posesión mediante su uso local.
        # Los nuevos registros públicos se verifican en AuthService.
        conexion.execute(text(
            "UPDATE usuarios SET correo_verificado_en = creado_en "
            "WHERE correo_verificado_en IS NULL"
        ))


def _migrar_mfa(conexion):
    if "usuarios" not in set(inspect(engine).get_table_names()):
        return
    columnas = {columna["name"] for columna in inspect(engine).get_columns("usuarios")}
    if "mfa_secret_encrypted" not in columnas:
        conexion.execute(text("ALTER TABLE usuarios ADD COLUMN mfa_secret_encrypted TEXT"))
    if "mfa_habilitado" not in columnas:
        conexion.execute(text("ALTER TABLE usuarios ADD COLUMN mfa_habilitado INTEGER NOT NULL DEFAULT 0"))


def _migrar_mfa_antireplay(conexion):
    if "usuarios" not in set(inspect(engine).get_table_names()):
        return
    columnas = {columna["name"] for columna in inspect(engine).get_columns("usuarios")}
    if "mfa_ultimo_contador_usado" not in columnas:
        conexion.execute(text("ALTER TABLE usuarios ADD COLUMN mfa_ultimo_contador_usado BIGINT"))


def _migrar_sesiones_seguras(conexion):
    if "sesiones_usuario" not in set(inspect(engine).get_table_names()):
        return
    columnas = {columna["name"] for columna in inspect(engine).get_columns("sesiones_usuario")}
    if "dispositivo" not in columnas:
        conexion.execute(text("ALTER TABLE sesiones_usuario ADD COLUMN dispositivo VARCHAR(160) NOT NULL DEFAULT 'Dispositivo desconocido'"))
    if "ip_hash" not in columnas:
        conexion.execute(text("ALTER TABLE sesiones_usuario ADD COLUMN ip_hash VARCHAR(64)"))


def _migrar_dinero_decimal(conexion):
    """Normaliza columnas monetarias; SQLite conserva afinidad dinámica y valida en servicios."""
    if engine.dialect.name != "postgresql":
        return
    columnas = {
        "cuentas": ("saldo",), "movimientos": ("valor",),
        "operaciones_detectadas": ("valor",), "gastos_recurrentes": ("valor",),
        "transferencias": ("valor",), "presupuestos": ("valor",),
        "metas": ("objetivo", "ahorrado"), "meta_operaciones": ("valor_meta",),
        "inversiones": ("cantidad", "precio_compra", "precio_actual"),
        "tasas_cambio": ("tasa",),
    }
    tablas = set(inspect(engine).get_table_names())
    for tabla, nombres in columnas.items():
        if tabla not in tablas:
            continue
        presentes = {columna["name"]: columna for columna in inspect(engine).get_columns(tabla)}
        for nombre in nombres:
            columna = presentes.get(nombre)
            tipo = columna and columna["type"]
            if columna and not (
                isinstance(tipo, Numeric)
                and tipo.precision == 24
                and tipo.scale == 8
            ):
                conexion.execute(text(
                    f'ALTER TABLE "{tabla}" ALTER COLUMN "{nombre}" '
                    f'TYPE NUMERIC(24, 8) USING ROUND("{nombre}"::numeric, 8)'
                ))


def _migrar_inversiones_trazables(conexion):
    """Añade procedencia contable sin reinterpretar posiciones históricas."""
    if "inversiones" not in set(inspect(engine).get_table_names()):
        return
    columnas = {columna["name"] for columna in inspect(engine).get_columns("inversiones")}
    booleano = "BOOLEAN" if engine.dialect.name == "postgresql" else "INTEGER"
    verdadero = "TRUE" if engine.dialect.name == "postgresql" else "1"
    cambios = {
        "fecha_apertura": "DATE",
        "es_posicion_inicial": f"{booleano} NOT NULL DEFAULT {verdadero}",
        "valores_totales": f"{booleano} NOT NULL DEFAULT {'FALSE' if engine.dialect.name == 'postgresql' else '0'}",
        "cuenta_origen_id": "INTEGER REFERENCES cuentas(id)",
        "movimiento_aporte_id": "INTEGER REFERENCES movimientos(id)",
    }
    for nombre, definicion in cambios.items():
        if nombre not in columnas:
            conexion.execute(text(f"ALTER TABLE inversiones ADD COLUMN {nombre} {definicion}"))
    conexion.execute(text("UPDATE inversiones SET fecha_apertura = CURRENT_DATE WHERE fecha_apertura IS NULL"))
    conexion.execute(text("CREATE INDEX IF NOT EXISTS ix_inversiones_cuenta_origen_id ON inversiones (cuenta_origen_id)"))
    conexion.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_inversiones_movimiento_aporte_id ON inversiones (movimiento_aporte_id) WHERE movimiento_aporte_id IS NOT NULL"))


def _migrar_cuentas_producto(conexion):
    """Conserva el histórico al permitir desactivar productos financieros."""
    if "cuentas" not in set(inspect(engine).get_table_names()):
        return
    columnas = {columna["name"] for columna in inspect(engine).get_columns("cuentas")}
    cambios = {
        "institucion": "VARCHAR(100) NOT NULL DEFAULT ''",
        "activa": "INTEGER NOT NULL DEFAULT 1",
        # SQLite rechaza funciones como CURRENT_TIMESTAMP al añadir columnas.
        # Se añade sin default y se completa en una segunda sentencia segura.
        "actualizada_en": (
            "DATETIME" if engine.dialect.name == "sqlite"
            else "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"
        ),
    }
    for nombre, definicion in cambios.items():
        if nombre not in columnas:
            conexion.execute(text(f"ALTER TABLE cuentas ADD COLUMN {nombre} {definicion}"))
    conexion.execute(text(
        "UPDATE cuentas SET actualizada_en = CURRENT_TIMESTAMP "
        "WHERE actualizada_en IS NULL"
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
        ("007_roles_publicacion", _migrar_roles_publicacion),
        ("008_seguridad_cuentas", _migrar_seguridad_cuentas),
        ("009_mfa", _migrar_mfa),
        ("010_sesiones_seguras", _migrar_sesiones_seguras),
        ("011_dinero_decimal", _migrar_dinero_decimal),
        ("012_mfa_antireplay", _migrar_mfa_antireplay),
        ("013_inversiones_trazables", _migrar_inversiones_trazables),
        ("014_cuentas_producto", _migrar_cuentas_producto),
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
