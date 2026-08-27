from datetime import date, datetime

from pydantic import BaseModel as PydanticBaseModel, ConfigDict, Field


class BaseModel(PydanticBaseModel):
    """Contrato API común: JSON financiero nunca admite NaN ni infinitos."""

    model_config = ConfigDict(allow_inf_nan=False)


class RegistroPropietario(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    correo: str = Field(min_length=5, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=12, max_length=128)


class InicioSesion(BaseModel):
    correo: str = Field(min_length=5, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=1, max_length=128)
    mfa_codigo: str | None = Field(default=None, pattern=r"^\d{6}$")


class SolicitudRecuperacion(BaseModel):
    correo: str = Field(min_length=5, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class TokenAccion(BaseModel):
    token: str = Field(min_length=32, max_length=200)


class RestablecerPassword(TokenAccion):
    password: str = Field(min_length=12, max_length=128)


class SesionMovilRespuesta(BaseModel):
    usuario: "UsuarioRespuesta"
    token: str
    vence_en_segundos: int = 43200


class SesionActivaRespuesta(BaseModel):
    id: int
    dispositivo: str
    creada_en: datetime
    ultima_actividad: datetime
    vence_en: datetime
    actual: bool


class CodigoMfa(BaseModel):
    codigo: str = Field(pattern=r"^\d{6}$")


class DesactivarMfa(CodigoMfa):
    password: str = Field(min_length=1, max_length=128)


class UsuarioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nombre: str
    correo: str
    rol: str
    activo: bool
    mfa_habilitado: bool = False


class UsuarioCrearAdmin(RegistroPropietario):
    pass


class UsuarioActualizarAdmin(BaseModel):
    activo: bool


class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CuentaCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    tipo: str = Field(min_length=1, max_length=50)
    saldo: float = Field(default=0, ge=-1_000_000_000_000, le=1_000_000_000_000)
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


class CuentaActualizar(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    tipo: str = Field(min_length=1, max_length=50)
    moneda: str = "COP"
    color: str = "#2563EB"
    icono: str = "🏦"


class CategoriaGuardar(BaseModel):
    nombre: str = Field(min_length=1, max_length=80)
    tipo: str
    color: str = "#4CAF50"
    icono: str = "🏷️"
    grupo: str = "Otros"
    orden: int = 0


class CategoriaActualizar(CategoriaGuardar):
    activa: bool = True


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
    huella: str | None = Field(default=None, min_length=16, max_length=64)


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


class TarjetaCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    banco: str = Field(default="", max_length=100)
    ultimos_cuatro: str = Field(min_length=4, max_length=19)
    tipo: str
    moneda: str = "COP"
    cuenta_id: int | None = None


class TarjetaRespuesta(ORMResponse):
    id: int
    nombre: str
    banco: str
    ultimos_cuatro: str
    tipo: str
    moneda: str
    cuenta_id: int
    activa: bool
    cuenta: str
    cuenta_tipo: str
    saldo: float


class PagoTarjetaCrear(BaseModel):
    cuenta_origen_id: int
    valor: float = Field(gt=0)
    fecha: date
    descripcion: str = Field(default="", max_length=250)


class DeteccionCrear(BaseModel):
    texto: str = Field(min_length=3, max_length=4000)
    origen: str = Field(default="Manual", max_length=30)


class DeteccionConfirmar(BaseModel):
    categoria_id: int
    tarjeta_id: int | None = None
    cuenta_id: int | None = None
    descripcion: str | None = Field(default=None, max_length=250)


class DeteccionRespuesta(ORMResponse):
    id: int
    origen: str
    comercio: str
    valor: float
    moneda: str
    fecha: datetime
    banco: str
    ultimos_cuatro: str | None
    tipo_sugerido: str | None
    estado: str
    tarjeta_id: int | None
    movimiento_id: int | None
    duplicada: bool = False


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


class GastoRecurrenteActualizar(GastoRecurrenteCrear):
    activo: bool = True


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


class TasaCambioRespuesta(BaseModel):
    id: int
    moneda_origen: str
    moneda_destino: str
    tasa: float
    fuente: str | None
    fecha_actualizacion: datetime


class ActualizacionTasasRespuesta(BaseModel):
    actualizadas: bool
    moneda_base: str
    ultima_actualizacion: datetime | None
    total: int


class AdjuntoRespuesta(ORMResponse):
    id: int
    movimiento_id: int
    nombre: str
    tipo_mime: str
    tamano: int
    fecha: datetime
    url_descarga: str


class InversionGuardar(BaseModel):
    activo: str = Field(min_length=1, max_length=100)
    tipo: str = Field(min_length=1, max_length=50)
    cantidad: float = Field(gt=0)
    precio_compra: float = Field(gt=0)
    precio_actual: float = Field(gt=0)
    broker: str = ""
    moneda: str = "USD"
    valores_totales: bool = False
    fecha_apertura: date = Field(default_factory=date.today)
    es_posicion_inicial: bool = True
    cuenta_origen_id: int | None = None


class InversionRespuesta(ORMResponse):
    id: int
    activo: str
    tipo: str
    cantidad: float
    precio_compra: float
    precio_actual: float
    broker: str | None
    moneda: str
    valores_totales: bool
    fecha_apertura: date
    es_posicion_inicial: bool
    cuenta_origen_id: int | None
    cuenta_origen: str | None
    movimiento_aporte_id: int | None
    costo: float
    valor: float
    ganancia: float
    rentabilidad: float
    costo_cop: float | None
    valor_cop: float | None


class PortafolioRespuesta(BaseModel):
    costo_total_cop: float
    valor_total_cop: float
    ganancia_total_cop: float
    rentabilidad: float
    posiciones: list[InversionRespuesta]
    monedas_sin_tasa: list[str]
