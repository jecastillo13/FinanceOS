from datetime import datetime, date

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    ForeignKey,
    Text
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