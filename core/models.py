from datetime import datetime, date

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    ForeignKey,
    Text,
    UniqueConstraint,
)

from sqlalchemy.orm import relationship

from core.database import Base


# =====================================================
# CUENTAS
# =====================================================

class Cuenta(Base):
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
        Float,
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

class Categoria(Base):
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

class Movimiento(Base):
    __tablename__ = "movimientos"

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
        Float,
        nullable=False
    )

    observaciones = Column(
        Text
    )

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


class Tarjeta(Base):
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


class OperacionDetectada(Base):
    __tablename__ = "operaciones_detectadas"
    __table_args__ = (UniqueConstraint("huella", name="uq_operacion_detectada_huella"),)

    id = Column(Integer, primary_key=True)
    origen = Column(String(30), nullable=False, default="Manual")
    texto_original = Column(Text, nullable=False)
    comercio = Column(String(160), nullable=False, default="Compra detectada")
    valor = Column(Float, nullable=False)
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


class AdjuntoMovimiento(Base):
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

class GastoRecurrente(Base):
    __tablename__ = "gastos_recurrentes"

    id = Column(Integer, primary_key=True)
    nombre = Column(String(120), nullable=False)
    valor = Column(Float, nullable=False)
    frecuencia = Column(String(20), nullable=False, default="Mensual")
    proxima_fecha_pago = Column(Date, nullable=False)
    ultima_fecha_pago = Column(Date)
    activo = Column(Integer, nullable=False, default=1)

    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    categoria = relationship("Categoria")


# =====================================================
# TRANSFERENCIAS ENTRE CUENTAS
# =====================================================

class Transferencia(Base):
    __tablename__ = "transferencias"

    id = Column(Integer, primary_key=True)
    fecha = Column(Date, default=date.today, nullable=False)
    valor = Column(Float, nullable=False)
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

class Presupuesto(Base):
    __tablename__ = "presupuestos"

    id = Column(Integer, primary_key=True)
    anio = Column(Integer, nullable=False)
    mes = Column(Integer, nullable=False)
    valor = Column(Float, nullable=False)
    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)

    categoria = relationship("Categoria")


# =====================================================
# METAS
# =====================================================

class Meta(Base):
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
        Float
    )

    ahorrado = Column(
        Float,
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


class MetaOperacion(Base):
    __tablename__ = "meta_operaciones"

    id = Column(Integer, primary_key=True)
    meta_id = Column(Integer, ForeignKey("metas.id"), nullable=False)
    movimiento_id = Column(Integer, ForeignKey("movimientos.id"), nullable=True)
    tipo = Column(String(20), nullable=False)
    valor_meta = Column(Float, nullable=False)
    fecha = Column(Date, default=date.today, nullable=False)
    descripcion = Column(String(250), default="")

    meta = relationship("Meta", back_populates="operaciones")
    movimiento = relationship("Movimiento")


# =====================================================
# INVERSIONES
# =====================================================

class Inversion(Base):
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
        Float
    )

    precio_compra = Column(
        Float
    )

    precio_actual = Column(
        Float
    )

    broker = Column(
        String(100)
    )

    moneda = Column(
        String(10),
        default="USD"
    )


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

class Auditoria(Base):
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
        Float,
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
