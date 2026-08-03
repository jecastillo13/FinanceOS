"""Punto de entrada de la API local de FinanceOS."""

from urllib.parse import quote

from fastapi import FastAPI, File, HTTPException, Query, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from api.schemas import (
    AdjuntoRespuesta, CategoriaActualizar, CategoriaGuardar, CategoriaRespuesta,
    ConversionRespuesta, CuentaActualizar, CuentaCrear, CuentaRespuesta,
    GastoRecurrenteActualizar, GastoRecurrenteCrear, GastoRecurrenteRespuesta,
    InversionGuardar, InversionRespuesta,
    MetaCrear, MetaDetalleRespuesta, MetaOperacionCrear, MetaOperacionRespuesta,
    MetaPagoCrear, MetaRespuesta, MovimientoCrear, MovimientoRespuesta, PagoRecurrenteCrear,
    PortafolioRespuesta, PresupuestoGuardar, PresupuestoRespuesta,
    TransferenciaCrear, TransferenciaRespuesta,
)
from core.database import create_database
from core.services import (
    AccountService, AttachmentService, BudgetService, CategoryService, DashboardService,
    ExchangeService, GoalService, InvestmentService, MovementService,
    RecurringExpenseService, ReportService, TransferService,
)


app = FastAPI(title="FinanceOS API", version="0.1.0", description="API local preparada para las aplicaciones web y móvil de FinanceOS.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:3000", "http://localhost:5173"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
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


@app.get("/api/v1/cuentas/{cuenta_id}", response_model=CuentaRespuesta)
def detalle_cuenta(cuenta_id: int):
    service = AccountService()
    try:
        cuenta = service.obtener_cuenta(cuenta_id)
        if cuenta is None:
            raise HTTPException(status_code=404, detail="La cuenta no existe.")
        return cuenta
    finally:
        service.cerrar()


@app.put("/api/v1/cuentas/{cuenta_id}", response_model=CuentaRespuesta)
def actualizar_cuenta(cuenta_id: int, datos: CuentaActualizar):
    service = AccountService()
    try:
        cuenta = service.obtener_cuenta(cuenta_id)
        if cuenta is None:
            raise HTTPException(status_code=404, detail="La cuenta no existe.")
        return service.actualizar_cuenta(cuenta_id, saldo=cuenta.saldo, **datos.model_dump())
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.delete("/api/v1/cuentas/{cuenta_id}", status_code=204, response_class=Response)
def eliminar_cuenta(cuenta_id: int):
    service = AccountService()
    try:
        if service.obtener_cuenta(cuenta_id) is None:
            raise HTTPException(status_code=404, detail="La cuenta no existe.")
        if not service.eliminar_cuenta(cuenta_id):
            raise HTTPException(status_code=409, detail="La cuenta tiene movimientos y no puede eliminarse.")
        return Response(status_code=204)
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


@app.post("/api/v1/categorias", response_model=CategoriaRespuesta, status_code=201)
def crear_categoria(datos: CategoriaGuardar):
    service = CategoryService()
    try:
        return service.crear_categoria(**datos.model_dump())
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.put("/api/v1/categorias/{categoria_id}", response_model=CategoriaRespuesta)
def actualizar_categoria(categoria_id: int, datos: CategoriaActualizar):
    service = CategoryService()
    try:
        categoria = service.actualizar_categoria(categoria_id, **datos.model_dump())
        if categoria is None:
            raise HTTPException(status_code=404, detail="La categoría no existe.")
        return categoria
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.delete("/api/v1/categorias/{categoria_id}", status_code=204, response_class=Response)
def eliminar_categoria(categoria_id: int):
    service = CategoryService()
    try:
        if service.obtener_categoria(categoria_id) is None:
            raise HTTPException(status_code=404, detail="La categoría no existe.")
        if not service.eliminar_categoria(categoria_id):
            raise HTTPException(status_code=409, detail="La categoría está relacionada con movimientos y no puede eliminarse.")
        return Response(status_code=204)
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


@app.get("/api/v1/movimientos/{movimiento_id}", response_model=MovimientoRespuesta)
def detalle_movimiento(movimiento_id: int):
    service = MovementService()
    try:
        movimiento = service.obtener_movimiento(movimiento_id)
        if movimiento is None:
            raise HTTPException(status_code=404, detail="El movimiento no existe.")
        return _serializar_movimiento(movimiento)
    finally:
        service.cerrar()


@app.put("/api/v1/movimientos/{movimiento_id}", response_model=MovimientoRespuesta)
def actualizar_movimiento(movimiento_id: int, datos: MovimientoCrear):
    service = MovementService()
    try:
        movimiento = service.actualizar_movimiento(movimiento_id, **datos.model_dump())
        if movimiento is None:
            raise HTTPException(status_code=404, detail="El movimiento no existe.")
        return _serializar_movimiento(movimiento)
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.delete("/api/v1/movimientos/{movimiento_id}", status_code=204, response_class=Response)
def eliminar_movimiento(movimiento_id: int):
    service = MovementService()
    try:
        if service.obtener_movimiento(movimiento_id) is None:
            raise HTTPException(status_code=404, detail="El movimiento no existe.")
        service.eliminar_movimiento(movimiento_id)
        return Response(status_code=204)
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


@app.get("/api/v1/metas/{meta_id}", response_model=MetaDetalleRespuesta)
def detalle_meta(meta_id: int):
    service = GoalService()
    try:
        meta = service.obtener_meta(meta_id)
        if meta is None:
            raise HTTPException(status_code=404, detail="La meta no existe.")
        return _serializar_meta_detalle(service.resumen(meta))
    finally:
        service.cerrar()


@app.post("/api/v1/metas/{meta_id}/aportes", response_model=MetaOperacionRespuesta, status_code=201)
def aportar_meta(meta_id: int, datos: MetaOperacionCrear):
    service = GoalService()
    try:
        return _serializar_operacion(service.aportar(meta_id, **datos.model_dump()))
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.post("/api/v1/metas/{meta_id}/pagos", response_model=MetaOperacionRespuesta, status_code=201)
def pagar_meta(meta_id: int, datos: MetaPagoCrear):
    service = GoalService()
    try:
        return _serializar_operacion(service.registrar_pago(meta_id, **datos.model_dump()))
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.delete("/api/v1/metas/operaciones/{operacion_id}", status_code=204, response_class=Response)
def eliminar_operacion_meta(operacion_id: int):
    service = GoalService()
    try:
        if not service.eliminar_operacion(operacion_id):
            raise HTTPException(status_code=404, detail="La operación de la meta no existe.")
        return Response(status_code=204)
    finally:
        service.cerrar()


@app.delete("/api/v1/metas/{meta_id}", status_code=204, response_class=Response)
def eliminar_meta(meta_id: int):
    service = GoalService()
    try:
        if not service.eliminar_meta(meta_id):
            raise HTTPException(status_code=404, detail="La meta no existe.")
        return Response(status_code=204)
    finally:
        service.cerrar()


@app.get("/api/v1/movimientos/{movimiento_id}/comprobantes", response_model=list[AdjuntoRespuesta])
def listar_comprobantes(movimiento_id: int):
    service = AttachmentService()
    try:
        return [_serializar_adjunto(adjunto) for adjunto in service.obtener_por_movimiento(movimiento_id)]
    finally:
        service.cerrar()


@app.post("/api/v1/movimientos/{movimiento_id}/comprobantes", response_model=AdjuntoRespuesta, status_code=201)
async def adjuntar_comprobante(movimiento_id: int, archivo: UploadFile = File(...)):
    service = AttachmentService()
    try:
        contenido = await archivo.read(service.TAMANO_MAXIMO + 1)
        adjunto = service.guardar(movimiento_id, archivo.filename or "comprobante", contenido, archivo.content_type or "")
        return _serializar_adjunto(adjunto)
    except ValueError as error:
        _error_negocio(error)
    finally:
        await archivo.close()
        service.cerrar()


@app.get("/api/v1/comprobantes/{adjunto_id}")
def descargar_comprobante(adjunto_id: int):
    service = AttachmentService()
    try:
        adjunto = service.obtener(adjunto_id)
        if adjunto is None:
            raise HTTPException(status_code=404, detail="El comprobante no existe.")
        contenido = service.leer(adjunto)
        if contenido is None:
            raise HTTPException(status_code=404, detail="El archivo del comprobante no está disponible.")
        nombre = quote(adjunto.nombre)
        return Response(content=contenido, media_type=adjunto.tipo_mime, headers={"Content-Disposition": f"attachment; filename*=UTF-8''{nombre}"})
    finally:
        service.cerrar()


@app.delete("/api/v1/comprobantes/{adjunto_id}", status_code=204, response_class=Response)
def eliminar_comprobante(adjunto_id: int):
    service = AttachmentService()
    try:
        if not service.eliminar(adjunto_id):
            raise HTTPException(status_code=404, detail="El comprobante no existe.")
        return Response(status_code=204)
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


@app.put("/api/v1/gastos-recurrentes/{gasto_id}", response_model=GastoRecurrenteRespuesta)
def actualizar_gasto_recurrente(gasto_id: int, datos: GastoRecurrenteActualizar):
    service = RecurringExpenseService()
    try:
        gasto = service.actualizar_gasto(gasto_id, **datos.model_dump())
        if gasto is None:
            raise HTTPException(status_code=404, detail="El gasto recurrente no existe.")
        return _serializar_recurrente(gasto)
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.delete("/api/v1/gastos-recurrentes/{gasto_id}", status_code=204, response_class=Response)
def eliminar_gasto_recurrente(gasto_id: int):
    service = RecurringExpenseService()
    try:
        if not service.eliminar_gasto(gasto_id):
            raise HTTPException(status_code=404, detail="El gasto recurrente no existe.")
        return Response(status_code=204)
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


@app.delete("/api/v1/transferencias/{transferencia_id}", status_code=204, response_class=Response)
def eliminar_transferencia(transferencia_id: int):
    service = TransferService()
    try:
        if not service.eliminar_transferencia(transferencia_id):
            raise HTTPException(status_code=404, detail="La transferencia no existe.")
        return Response(status_code=204)
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


@app.delete("/api/v1/presupuestos/{presupuesto_id}", status_code=204, response_class=Response)
def eliminar_presupuesto(presupuesto_id: int):
    service = BudgetService()
    try:
        if not service.eliminar_presupuesto(presupuesto_id):
            raise HTTPException(status_code=404, detail="El presupuesto no existe.")
        return Response(status_code=204)
    finally:
        service.cerrar()


@app.get("/api/v1/inversiones", response_model=PortafolioRespuesta)
def listar_inversiones():
    service = InvestmentService()
    try:
        resumen = service.resumen("COP")
        return PortafolioRespuesta(
            costo_total_cop=resumen["costo_total"],
            valor_total_cop=resumen["valor_total"],
            ganancia_total_cop=resumen["ganancia_total"],
            rentabilidad=resumen["rentabilidad"],
            posiciones=[_serializar_inversion(service.resumen_posicion(inversion, "COP")) for inversion in service.obtener_inversiones()],
            monedas_sin_tasa=sorted({inversion.moneda for inversion in resumen["sin_tasa"]}),
        )
    finally:
        service.cerrar()


@app.post("/api/v1/inversiones", response_model=InversionRespuesta, status_code=201)
def crear_inversion(datos: InversionGuardar):
    service = InvestmentService()
    try:
        inversion = service.crear_inversion(**datos.model_dump())
        return _serializar_inversion(service.resumen_posicion(inversion, "COP"))
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.put("/api/v1/inversiones/{inversion_id}", response_model=InversionRespuesta)
def actualizar_inversion(inversion_id: int, datos: InversionGuardar):
    service = InvestmentService()
    try:
        inversion = service.actualizar_inversion(inversion_id, **datos.model_dump())
        if inversion is None:
            raise HTTPException(status_code=404, detail="La inversión no existe.")
        return _serializar_inversion(service.resumen_posicion(inversion, "COP"))
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.delete("/api/v1/inversiones/{inversion_id}", status_code=204, response_class=Response)
def eliminar_inversion(inversion_id: int):
    service = InvestmentService()
    try:
        if not service.eliminar_inversion(inversion_id):
            raise HTTPException(status_code=404, detail="La inversión no existe.")
        return Response(status_code=204)
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


@app.get("/api/v1/reportes/{anio}/{mes}/resumen")
def resumen_reporte(anio: int, mes: int):
    if not 2000 <= anio <= 2100 or not 1 <= mes <= 12:
        raise HTTPException(status_code=400, detail="El período solicitado no es válido.")
    service = ReportService()
    try:
        reporte = service.obtener_reporte(anio, mes)
        return {clave: valor for clave, valor in reporte.items() if clave != "filas"} | {"movimientos": len(reporte["filas"])}
    finally:
        service.cerrar()


@app.get("/api/v1/reportes/{anio}/{mes}/{formato}")
def descargar_reporte(anio: int, mes: int, formato: str):
    if not 2000 <= anio <= 2100 or not 1 <= mes <= 12:
        raise HTTPException(status_code=400, detail="El período solicitado no es válido.")
    generadores = {
        "csv": ("generar_csv", "text/csv"),
        "xlsx": ("generar_excel", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        "pdf": ("generar_pdf", "application/pdf"),
    }
    if formato not in generadores:
        raise HTTPException(status_code=404, detail="Formato no disponible. Usa csv, xlsx o pdf.")
    service = ReportService()
    try:
        metodo, tipo_mime = generadores[formato]
        contenido = getattr(service, metodo)(service.obtener_reporte(anio, mes))
        nombre = f"financeos_{anio}_{mes:02d}.{formato}"
        return Response(contenido, media_type=tipo_mime, headers={"Content-Disposition": f'attachment; filename="{nombre}"'})
    finally:
        service.cerrar()


def _serializar_movimiento(movimiento):
    return MovimientoRespuesta(id=movimiento.id, fecha=movimiento.fecha, descripcion=movimiento.descripcion, valor=movimiento.valor, observaciones=movimiento.observaciones, cuenta_id=movimiento.cuenta_id, categoria_id=movimiento.categoria_id, cuenta=movimiento.cuenta.nombre, moneda=movimiento.cuenta.moneda, categoria=movimiento.categoria.nombre, tipo=movimiento.categoria.tipo)


def _serializar_meta(resumen):
    meta = resumen["meta"]
    return MetaRespuesta(id=meta.id, nombre=meta.nombre, objetivo=meta.objetivo, moneda=meta.moneda, fecha_limite=meta.fecha_limite, descripcion=meta.descripcion, pagado=resumen["pagado"], aportado=resumen["aportado"], pendiente=resumen["pendiente"], porcentaje=resumen["porcentaje"])


def _serializar_meta_detalle(resumen):
    meta = _serializar_meta(resumen)
    return MetaDetalleRespuesta(**meta.model_dump(), operaciones=[_serializar_operacion(operacion) for operacion in resumen["operaciones"]])


def _serializar_operacion(operacion):
    return MetaOperacionRespuesta.model_validate(operacion)


def _serializar_adjunto(adjunto):
    return AdjuntoRespuesta(id=adjunto.id, movimiento_id=adjunto.movimiento_id, nombre=adjunto.nombre, tipo_mime=adjunto.tipo_mime, tamano=adjunto.tamano, fecha=adjunto.fecha, url_descarga=f"/api/v1/comprobantes/{adjunto.id}")


def _serializar_recurrente(gasto):
    return GastoRecurrenteRespuesta(id=gasto.id, nombre=gasto.nombre, valor=gasto.valor, frecuencia=gasto.frecuencia, proxima_fecha_pago=gasto.proxima_fecha_pago, ultima_fecha_pago=gasto.ultima_fecha_pago, activo=bool(gasto.activo), categoria_id=gasto.categoria_id, categoria=gasto.categoria.nombre)


def _serializar_transferencia(transferencia):
    return TransferenciaRespuesta(id=transferencia.id, fecha=transferencia.fecha, valor=transferencia.valor, descripcion=transferencia.descripcion, cuenta_origen_id=transferencia.cuenta_origen_id, cuenta_destino_id=transferencia.cuenta_destino_id, cuenta_origen=transferencia.cuenta_origen.nombre, cuenta_destino=transferencia.cuenta_destino.nombre, moneda=transferencia.cuenta_origen.moneda)


def _serializar_presupuesto(item):
    presupuesto = item["presupuesto"]
    return PresupuestoRespuesta(id=presupuesto.id, anio=presupuesto.anio, mes=presupuesto.mes, valor=presupuesto.valor, categoria_id=presupuesto.categoria_id, categoria=presupuesto.categoria.nombre, gastado=item["gastado"])


def _serializar_inversion(item):
    inversion = item["inversion"]
    return InversionRespuesta(
        id=inversion.id,
        activo=inversion.activo,
        tipo=inversion.tipo,
        cantidad=inversion.cantidad,
        precio_compra=inversion.precio_compra,
        precio_actual=inversion.precio_actual,
        broker=inversion.broker,
        moneda=inversion.moneda,
        costo=item["costo"],
        valor=item["valor"],
        ganancia=item["ganancia"],
        rentabilidad=item["rentabilidad"],
        costo_cop=item["costo_base"],
        valor_cop=item["valor_base"],
    )
