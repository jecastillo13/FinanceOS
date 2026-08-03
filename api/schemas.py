from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CuentaCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    tipo: str = Field(min_length=1, max_length=50)
    saldo: float = 0
    moneda: str = "COP"
    color: str = "#2563EB"
    icono: str = "🏦"


class CuentaRespuesta(ORMResponse):
    id: int
    nombre: str
    tipo: str
    saldo: float
    moneda: str
    color: str
    icono: str


class CategoriaRespuesta(ORMResponse):
    id: int
    nombre: str
    tipo: str
    color: str
    icono: str | None
    grupo: str | None
    activa: bool


class MovimientoCrear(BaseModel):
    fecha: date
    descripcion: str = Field(min_length=1, max_length=250)
    valor: float = Field(gt=0)
    cuenta_id: int
    categoria_id: int
    observaciones: str = ""


class MovimientoRespuesta(ORMResponse):
    id: int
    fecha: date
    descripcion: str | None
    valor: float
    observaciones: str | None
    cuenta_id: int
    categoria_id: int
    cuenta: str
    moneda: str
    categoria: str
    tipo: str


class MetaCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    objetivo: float = Field(gt=0)
    moneda: str = "COP"
    fecha_limite: date | None = None
    descripcion: str = ""


class MetaRespuesta(ORMResponse):
    id: int
    nombre: str
    objetivo: float
    moneda: str
    fecha_limite: date | None
    descripcion: str | None
    pagado: float
    aportado: float
    pendiente: float
    porcentaje: float


class MetaOperacionCrear(BaseModel):
    fecha: date
    valor: float = Field(gt=0)
    descripcion: str = ""


class MetaPagoCrear(MetaOperacionCrear):
    cuenta_id: int
    categoria_id: int
    observaciones: str = ""


class MetaOperacionRespuesta(ORMResponse):
    id: int
    meta_id: int
    movimiento_id: int | None
    tipo: str
    valor_meta: float
    fecha: date
    descripcion: str | None


class MetaDetalleRespuesta(MetaRespuesta):
    operaciones: list[MetaOperacionRespuesta]


class GastoRecurrenteCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    valor: float = Field(gt=0)
    frecuencia: str
    proxima_fecha_pago: date
    categoria_id: int


class GastoRecurrenteRespuesta(ORMResponse):
    id: int
    nombre: str
    valor: float
    frecuencia: str
    proxima_fecha_pago: date
    ultima_fecha_pago: date | None
    activo: bool
    categoria_id: int
    categoria: str


class PagoRecurrenteCrear(BaseModel):
    cuenta_id: int
    fecha_pago: date | None = None


class TransferenciaCrear(BaseModel):
    fecha: date
    cuenta_origen_id: int
    cuenta_destino_id: int
    valor: float = Field(gt=0)
    descripcion: str = ""


class TransferenciaRespuesta(ORMResponse):
    id: int
    fecha: date
    valor: float
    descripcion: str | None
    cuenta_origen_id: int
    cuenta_destino_id: int
    cuenta_origen: str
    cuenta_destino: str
    moneda: str


class PresupuestoGuardar(BaseModel):
    anio: int = Field(ge=2000, le=2100)
    mes: int = Field(ge=1, le=12)
    categoria_id: int
    valor: float = Field(gt=0)


class PresupuestoRespuesta(ORMResponse):
    id: int
    anio: int
    mes: int
    valor: float
    categoria_id: int
    categoria: str
    gastado: float


class ConversionRespuesta(BaseModel):
    valor_origen: float
    origen: str
    destino: str
    valor_convertido: float


class AdjuntoRespuesta(ORMResponse):
    id: int
    movimiento_id: int
    nombre: str
    tipo_mime: str
    tamano: int
    fecha: datetime
    url_descarga: str
