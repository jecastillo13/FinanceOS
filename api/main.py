"""Punto de entrada de la API local de FinanceOS."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from api.schemas import (
    CategoriaRespuesta, ConversionRespuesta, CuentaCrear, CuentaRespuesta,
    GastoRecurrenteCrear, GastoRecurrenteRespuesta, MetaCrear, MetaRespuesta,
    MovimientoCrear, MovimientoRespuesta, PagoRecurrenteCrear,
    PresupuestoGuardar, PresupuestoRespuesta, TransferenciaCrear, TransferenciaRespuesta,
)
from core.database import create_database
from core.services import (
    AccountService, BudgetService, CategoryService, DashboardService, ExchangeService,
    GoalService, MovementService, RecurringExpenseService, TransferService,
)


app = FastAPI(title="FinanceOS API", version="0.1.0", description="API local preparada para las aplicaciones web y móvil de FinanceOS.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _error_negocio(error):
    raise HTTPException(status_code=400, detail=str(error)) from error


@app.on_event("startup")
def iniciar_base_datos():
    create_database()


@app.get("/", include_in_schema=False)
def inicio():
    """Abre la documentación interactiva al entrar a la API local."""
    return RedirectResponse(url="/docs")


@app.get("/api/v1/health")
def health():
    return {"estado": "ok", "servicio": "financeos-api", "version": app.version}


@app.get("/api/v1/cuentas", response_model=list[CuentaRespuesta])
def listar_cuentas():
    service = AccountService()
    try:
        return service.obtener_cuentas()
    finally:
        service.cerrar()


@app.post("/api/v1/cuentas", response_model=CuentaRespuesta, status_code=201)
def crear_cuenta(datos: CuentaCrear):
    service = AccountService()
    try:
        return service.crear_cuenta(**datos.model_dump())
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.get("/api/v1/categorias", response_model=list[CategoriaRespuesta])
def listar_categorias(solo_activas: bool = True):
    service = CategoryService()
    try:
        categorias = service.obtener_categorias()
        return [categoria for categoria in categorias if categoria.activa] if solo_activas else categorias
    finally:
        service.cerrar()


@app.get("/api/v1/movimientos", response_model=list[MovimientoRespuesta])
def listar_movimientos(limite: int = Query(default=50, ge=1, le=100), pagina: int = Query(default=1, ge=1), busqueda: str = ""):
    service = MovementService()
    try:
        movimientos = service.obtener_movimientos(limite, (pagina - 1) * limite, busqueda)
        return [_serializar_movimiento(movimiento) for movimiento in movimientos]
    finally:
        service.cerrar()


@app.post("/api/v1/movimientos", response_model=MovimientoRespuesta, status_code=201)
def crear_movimiento(datos: MovimientoCrear):
    service = MovementService()
    try:
        return _serializar_movimiento(service.registrar_movimiento(**datos.model_dump()))
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.get("/api/v1/metas", response_model=list[MetaRespuesta])
def listar_metas():
    service = GoalService()
    try:
        return [_serializar_meta(service.resumen(meta)) for meta in service.obtener_metas()]
    finally:
        service.cerrar()


@app.post("/api/v1/metas", response_model=MetaRespuesta, status_code=201)
def crear_meta(datos: MetaCrear):
    service = GoalService()
    try:
        return _serializar_meta(service.resumen(service.crear_meta(**datos.model_dump())))
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.get("/api/v1/gastos-recurrentes", response_model=list[GastoRecurrenteRespuesta])
def listar_gastos_recurrentes(incluir_inactivos: bool = False):
    service = RecurringExpenseService()
    try:
        return [_serializar_recurrente(gasto) for gasto in service.obtener_gastos(incluir_inactivos)]
    finally:
        service.cerrar()


@app.post("/api/v1/gastos-recurrentes", response_model=GastoRecurrenteRespuesta, status_code=201)
def crear_gasto_recurrente(datos: GastoRecurrenteCrear):
    service = RecurringExpenseService()
    try:
        return _serializar_recurrente(service.crear_gasto(**datos.model_dump()))
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.post("/api/v1/gastos-recurrentes/{gasto_id}/pagar", response_model=MovimientoRespuesta)
def pagar_gasto_recurrente(gasto_id: int, datos: PagoRecurrenteCrear):
    service = RecurringExpenseService()
    try:
        return _serializar_movimiento(service.pagar(gasto_id, **datos.model_dump()))
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.get("/api/v1/transferencias", response_model=list[TransferenciaRespuesta])
def listar_transferencias():
    service = TransferService()
    try:
        return [_serializar_transferencia(transferencia) for transferencia in service.obtener_transferencias()]
    finally:
        service.cerrar()


@app.post("/api/v1/transferencias", response_model=TransferenciaRespuesta, status_code=201)
def crear_transferencia(datos: TransferenciaCrear):
    service = TransferService()
    try:
        return _serializar_transferencia(service.crear_transferencia(**datos.model_dump()))
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.get("/api/v1/presupuestos", response_model=list[PresupuestoRespuesta])
def listar_presupuestos(anio: int = Query(ge=2000, le=2100), mes: int = Query(ge=1, le=12)):
    service = BudgetService()
    try:
        return [_serializar_presupuesto(item) for item in service.resumen(anio, mes)]
    finally:
        service.cerrar()


@app.post("/api/v1/presupuestos", response_model=PresupuestoRespuesta, status_code=201)
def guardar_presupuesto(datos: PresupuestoGuardar):
    service = BudgetService()
    try:
        presupuesto = service.guardar_presupuesto(**datos.model_dump())
        return _serializar_presupuesto({"presupuesto": presupuesto, "gastado": service.gastado(presupuesto.categoria_id, presupuesto.anio, presupuesto.mes)})
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.get("/api/v1/monedas/convertir", response_model=ConversionRespuesta)
def convertir_moneda(valor: float = Query(gt=0), origen: str = "USD", destino: str = "COP"):
    service = ExchangeService()
    try:
        convertido = service.convertir(valor, origen.upper(), destino.upper())
        if convertido is None:
            raise HTTPException(status_code=404, detail="No hay una tasa disponible para esta conversión.")
        return ConversionRespuesta(valor_origen=valor, origen=origen.upper(), destino=destino.upper(), valor_convertido=convertido)
    finally:
        service.cerrar()


@app.get("/api/v1/dashboard/resumen")
def resumen_dashboard():
    service = DashboardService()
    try:
        resumen = service.resumen()
        pendientes = resumen.pop("pendientes", [])
        resumen["cuentas_sin_tasa"] = [
            {"id": cuenta.id, "nombre": cuenta.nombre, "moneda": cuenta.moneda}
            for cuenta in pendientes
        ]
        return resumen
    finally:
        service.cerrar()


def _serializar_movimiento(movimiento):
    return MovimientoRespuesta(id=movimiento.id, fecha=movimiento.fecha, descripcion=movimiento.descripcion, valor=movimiento.valor, observaciones=movimiento.observaciones, cuenta_id=movimiento.cuenta_id, categoria_id=movimiento.categoria_id, cuenta=movimiento.cuenta.nombre, moneda=movimiento.cuenta.moneda, categoria=movimiento.categoria.nombre, tipo=movimiento.categoria.tipo)


def _serializar_meta(resumen):
    meta = resumen["meta"]
    return MetaRespuesta(id=meta.id, nombre=meta.nombre, objetivo=meta.objetivo, moneda=meta.moneda, fecha_limite=meta.fecha_limite, descripcion=meta.descripcion, pagado=resumen["pagado"], aportado=resumen["aportado"], pendiente=resumen["pendiente"], porcentaje=resumen["porcentaje"])


def _serializar_recurrente(gasto):
    return GastoRecurrenteRespuesta(id=gasto.id, nombre=gasto.nombre, valor=gasto.valor, frecuencia=gasto.frecuencia, proxima_fecha_pago=gasto.proxima_fecha_pago, ultima_fecha_pago=gasto.ultima_fecha_pago, activo=bool(gasto.activo), categoria_id=gasto.categoria_id, categoria=gasto.categoria.nombre)


def _serializar_transferencia(transferencia):
    return TransferenciaRespuesta(id=transferencia.id, fecha=transferencia.fecha, valor=transferencia.valor, descripcion=transferencia.descripcion, cuenta_origen_id=transferencia.cuenta_origen_id, cuenta_destino_id=transferencia.cuenta_destino_id, cuenta_origen=transferencia.cuenta_origen.nombre, cuenta_destino=transferencia.cuenta_destino.nombre, moneda=transferencia.cuenta_origen.moneda)


def _serializar_presupuesto(item):
    presupuesto = item["presupuesto"]
    return PresupuestoRespuesta(id=presupuesto.id, anio=presupuesto.anio, mes=presupuesto.mes, valor=presupuesto.valor, categoria_id=presupuesto.categoria_id, categoria=presupuesto.categoria.nombre, gastado=item["gastado"])
