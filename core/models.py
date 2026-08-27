from datetime import datetime, date

from sqlalchemy import (
    Column,
    BigInteger,
    Boolean,
    Integer,
    String,
    Numeric,
    Date,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
)

from sqlalchemy.orm import relationship

from core.database import Base
from core.ownership import PropiedadUsuario


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    correo = Column(String(254), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    rol = Column(String(20), nullable=False, default="usuario")
    activo = Column(Integer, nullable=False, default=1)
    intentos_fallidos = Column(Integer, nullable=False, default=0)
    bloqueado_hasta = Column(DateTime)
    correo_verificado_en = Column(DateTime)
    mfa_secret_encrypted = Column(Text)
    mfa_habilitado = Column(Integer, nullable=False, default=0)
    mfa_ultimo_contador_usado = Column(BigInteger)
    creado_en = Column(DateTime, default=datetime.now, nullable=False)

    sesiones = relationship("SesionUsuario", back_populates="usuario", cascade="all, delete-orphan")
    tokens_seguridad = relationship("TokenSeguridadUsuario", back_populates="usuario", cascade="all, delete-orphan")


class SesionUsuario(Base):
    __tablename__ = "sesiones_usuario"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    creada_en = Column(DateTime, default=datetime.now, nullable=False)
    vence_en = Column(DateTime, nullable=False)
    revocada_en = Column(DateTime)
    ultima_actividad = Column(DateTime, default=datetime.now, nullable=False)
    dispositivo = Column(String(160), nullable=False, default="Dispositivo desconocido")
    ip_hash = Column(String(64))

    usuario = relationship("Usuario", back_populates="sesiones")


class IntentoAcceso(Base):
    """Contador compartido entre procesos para controles antiabuso."""

    __tablename__ = "intentos_acceso"

    clave = Column(String(255), primary_key=True)
    cantidad = Column(Integer, nullable=False, default=0)
    ventana_inicio = Column(DateTime, default=datetime.now, nullable=False)


class TokenSeguridadUsuario(Base):
    __tablename__ = "tokens_seguridad_usuario"

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    proposito = Column(String(30), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    creado_en = Column(DateTime, default=datetime.now, nullable=False)
    vence_en = Column(DateTime, nullable=False)
    usado_en = Column(DateTime)

    usuario = relationship("Usuario", back_populates="tokens_seguridad")


# =====================================================
# CUENTAS
# =====================================================

class Cuenta(PropiedadUsuario, Base):
    __tablename__ = "cuentas"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    nombre = Column(
        String(100),
        nullable=False
    )

    tipo = Column(
        String(50),
        nullable=False
    )

    saldo = Column(
        Numeric(24, 8),
        default=0
    )

    moneda = Column(
        String(10),
        default="COP"
    )

    color = Column(
        String(20),
        default="#2196F3"
    )

    icono = Column(
        String(50),
        default="🏦"
    )

    movimientos = relationship(
        "Movimiento",
        back_populates="cuenta",
        cascade="all, delete-orphan"
    )

    tarjetas = relationship("Tarjeta", back_populates="cuenta")


# =====================================================
# CATEGORÍAS
# =====================================================

class Categoria(PropiedadUsuario, Base):
    __tablename__ = "categorias"

    id = Column(
        Integer,
        primary_key=True
    )

    nombre = Column(
        String(80),
        nullable=False
    )

    tipo = Column(
        String(20),
        nullable=False
    )

    color = Column(
        String(20),
        default="#4CAF50"
    )

    icono = Column(String(50), default="🏷️")
    grupo = Column(String(80), default="Otros")
    es_sistema = Column(Integer, nullable=False, default=0)
    editable = Column(Integer, nullable=False, default=1)
    activa = Column(Integer, nullable=False, default=1)
    orden = Column(Integer, nullable=False, default=0)

    movimientos = relationship(
        "Movimiento",
        back_populates="categoria",
        cascade="all, delete-orphan"
    )


# =====================================================
# MOVIMIENTOS
# =====================================================

class Movimiento(PropiedadUsuario, Base):
    __tablename__ = "movimientos"
    __table_args__ = (UniqueConstraint("usuario_id", "huella", name="uq_movimiento_usuario_huella"),)

    id = Column(
        Integer,
        primary_key=True
    )

    fecha = Column(
        Date,
        default=date.today,
        nullable=False
    )

    descripcion = Column(
        String(250)
    )

    valor = Column(
        Numeric(24, 8),
        nullable=False
    )

    observaciones = Column(
        Text
    )

    # Identificador idempotente para importaciones (facturas, SMS y sincronizacion).
    # Es opcional para conservar los movimientos manuales historicos.
    huella = Column(String(64), nullable=True)

    cuenta_id = Column(
        Integer,
        ForeignKey("cuentas.id"),
        nullable=False
    )

    categoria_id = Column(
        Integer,
        ForeignKey("categorias.id"),
        nullable=False
    )

    cuenta = relationship(
        "Cuenta",
        back_populates="movimientos"
    )

    categoria = relationship(
        "Categoria",
        back_populates="movimientos"
    )

    adjuntos = relationship(
        "AdjuntoMovimiento",
        back_populates="movimiento",
        cascade="all, delete-orphan",
    )

    deteccion = relationship("OperacionDetectada", back_populates="movimiento", uselist=False)


class Tarjeta(PropiedadUsuario, Base):
    __tablename__ = "tarjetas"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), nullable=False)
    banco = Column(String(100), nullable=False, default="")
    ultimos_cuatro = Column(String(4), nullable=False)
    tipo = Column(String(10), nullable=False)
    moneda = Column(String(10), nullable=False, default="COP")
    cuenta_id = Column(Integer, ForeignKey("cuentas.id"), nullable=False)
    activa = Column(Integer, nullable=False, default=1)
    creada_en = Column(DateTime, default=datetime.now, nullable=False)

    cuenta = relationship("Cuenta", back_populates="tarjetas")


class OperacionDetectada(PropiedadUsuario, Base):
    __tablename__ = "operaciones_detectadas"
    __table_args__ = (UniqueConstraint("usuario_id", "huella", name="uq_operacion_usuario_huella"),)

    id = Column(Integer, primary_key=True)
    origen = Column(String(30), nullable=False, default="Manual")
    texto_original = Column(Text, nullable=False)
    comercio = Column(String(160), nullable=False, default="Compra detectada")
    valor = Column(Numeric(24, 8), nullable=False)
    moneda = Column(String(10), nullable=False, default="COP")
    fecha = Column(DateTime, default=datetime.now, nullable=False)
    banco = Column(String(100), nullable=False, default="")
    ultimos_cuatro = Column(String(4))
    tipo_sugerido = Column(String(10))
    estado = Column(String(20), nullable=False, default="Pendiente")
    huella = Column(String(64), nullable=False)
    tarjeta_id = Column(Integer, ForeignKey("tarjetas.id"))
    movimiento_id = Column(Integer, ForeignKey("movimientos.id"))
    creada_en = Column(DateTime, default=datetime.now, nullable=False)

    tarjeta = relationship("Tarjeta")
    movimiento = relationship("Movimiento", back_populates="deteccion")


class AdjuntoMovimiento(PropiedadUsuario, Base):
    __tablename__ = "adjuntos_movimiento"

    id = Column(Integer, primary_key=True)
    movimiento_id = Column(Integer, ForeignKey("movimientos.id"), nullable=False)
    nombre = Column(String(255), nullable=False)
    ruta = Column(String(500), nullable=False)
    tipo_mime = Column(String(100), nullable=False)
    tamano = Column(Integer, nullable=False)
    fecha = Column(DateTime, default=datetime.now, nullable=False)

    movimiento = relationship("Movimiento", back_populates="adjuntos")


# =====================================================
# GASTOS RECURRENTES
# =====================================================

class GastoRecurrente(PropiedadUsuario, Base):
    __tablename__ = "gastos_recurrentes"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(120), nullable=False)
    valor = Column(Numeric(24, 8), nullable=False)
    frecuencia = Column(String(20), nullable=False, default="Mensual")
    proxima_fecha_pago = Column(Date, nullable=False)
    ultima_fecha_pago = Column(Date)
    activo = Column(Integer, nullable=False, default=1)

    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    categoria = relationship("Categoria")


# =====================================================
# TRANSFERENCIAS ENTRE CUENTAS
# =====================================================

class Transferencia(PropiedadUsuario, Base):
    __tablename__ = "transferencias"

    id = Column(Integer, primary_key=True)
    fecha = Column(Date, default=date.today, nullable=False)
    valor = Column(Numeric(24, 8), nullable=False)
    descripcion = Column(String(250))
    cuenta_origen_id = Column(Integer, ForeignKey("cuentas.id"), nullable=False)
    cuenta_destino_id = Column(Integer, ForeignKey("cuentas.id"), nullable=False)
    movimiento_salida_id = Column(Integer, nullable=False)
    movimiento_entrada_id = Column(Integer, nullable=False)

    cuenta_origen = relationship("Cuenta", foreign_keys=[cuenta_origen_id])
    cuenta_destino = relationship("Cuenta", foreign_keys=[cuenta_destino_id])


# =====================================================
# PRESUPUESTOS MENSUALES
# =====================================================

class Presupuesto(PropiedadUsuario, Base):
    __tablename__ = "presupuestos"

    id = Column(Integer, primary_key=True)
    anio = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    valor = Column(Numeric(24, 8), nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)

    categoria = relationship("Categoria")


# =====================================================
# METAS
# =====================================================

class Meta(PropiedadUsuario, Base):
    __tablename__ = "metas"

    id = Column(
        Integer,
        primary_key=True
    )

    nombre = Column(
        String(100),
        nullable=False
    )

    objetivo = Column(
        Numeric(24, 8)
    )

    ahorrado = Column(
        Numeric(24, 8),
        default=0
    )

    fecha_limite = Column(
        Date
    )

    descripcion = Column(Text, default="")
    moneda = Column(String(10), nullable=False, default="COP")
    activa = Column(Integer, nullable=False, default=1)

    operaciones = relationship(
        "MetaOperacion",
        back_populates="meta",
        cascade="all, delete-orphan",
    )


class MetaOperacion(PropiedadUsuario, Base):
    __tablename__ = "meta_operaciones"

    id = Column(Integer, primary_key=True)
    meta_id = Column(Integer, ForeignKey("metas.id"), nullable=False)
    movimiento_id = Column(Integer, ForeignKey("movimientos.id"), nullable=True)
    tipo = Column(String(20), nullable=False)
    valor_meta = Column(Numeric(24, 8), nullable=False)
    fecha = Column(Date, default=date.today, nullable=False)
    descripcion = Column(String(250), default="")

    meta = relationship("Meta", back_populates="operaciones")
    movimiento = relationship("Movimiento")


# =====================================================
# INVERSIONES
# =====================================================

class Inversion(PropiedadUsuario, Base):
    __tablename__ = "inversiones"

    id = Column(
        Integer,
        primary_key=True
    )

    activo = Column(
        String(100)
    )

    tipo = Column(
        String(50)
    )

    cantidad = Column(
        Numeric(24, 8)
    )

    precio_compra = Column(
        Numeric(24, 8)
    )

    precio_actual = Column(
        Numeric(24, 8)
    )

    broker = Column(
        String(100)
    )

    moneda = Column(
        String(10),
        default="USD"
    )

    fecha_apertura = Column(Date, default=date.today, nullable=False)
    es_posicion_inicial = Column(Boolean, default=True, nullable=False)
    valores_totales = Column(Boolean, default=False, nullable=False)
    cuenta_origen_id = Column(Integer, ForeignKey("cuentas.id"), nullable=True, index=True)
    movimiento_aporte_id = Column(Integer, ForeignKey("movimientos.id"), nullable=True, unique=True)

    cuenta_origen = relationship("Cuenta", foreign_keys=[cuenta_origen_id])
    movimiento_aporte = relationship("Movimiento", foreign_keys=[movimiento_aporte_id])


# =====================================================
# CONFIGURACIÓN
# =====================================================

class Configuracion(Base):
    __tablename__ = "configuracion"

    id = Column(
        Integer,
        primary_key=True
    )

    clave = Column(
        String(100),
        unique=True
    )

    valor = Column(
        String(500)
    )


# =====================================================
# AUDITORÍA
# =====================================================

class Auditoria(PropiedadUsuario, Base):
    __tablename__ = "auditoria"

    id = Column(
        Integer,
        primary_key=True
    )

    accion = Column(
        String(100)
    )

    descripcion = Column(
        Text
    )

    fecha = Column(
        DateTime,
        default=datetime.now
    )

# =====================================================
# TASAS DE CAMBIO
# =====================================================

class TasaCambio(Base):
    __tablename__ = "tasas_cambio"

    id = Column(
        Integer,
        primary_key=True
    )

    moneda_origen = Column(
        String(10),
        nullable=False
    )

    moneda_destino = Column(
        String(10),
        nullable=False
    )

    tasa = Column(
        Numeric(24, 8),
        nullable=False
    )

    fuente = Column(
        String(100),
        default="ExchangeRate API"
    )

    fecha_actualizacion = Column(
        DateTime,
        default=datetime.now
    )
