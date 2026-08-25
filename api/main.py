"""Punto de entrada de la API local de FinanceOS."""

import os
from contextlib import asynccontextmanager
from ipaddress import ip_address
from pathlib import Path
from urllib.parse import quote, urlsplit

from fastapi import FastAPI, File, HTTPException, Query, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# La configuración privada se carga antes de importar la base de datos y los
# servicios, porque estos también consultan variables de entorno al iniciarse.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

from api.schemas import (
    AdjuntoRespuesta, CategoriaActualizar, CategoriaGuardar, CategoriaRespuesta,
    ConversionRespuesta, CuentaActualizar, CuentaCrear, CuentaRespuesta,
    GastoRecurrenteActualizar, GastoRecurrenteCrear, GastoRecurrenteRespuesta,
    InversionGuardar, InversionRespuesta,
    MetaCrear, MetaDetalleRespuesta, MetaOperacionCrear, MetaOperacionRespuesta,
    MetaPagoCrear, MetaRespuesta, MovimientoCrear, MovimientoRespuesta, PagoRecurrenteCrear,
    PortafolioRespuesta, PresupuestoGuardar, PresupuestoRespuesta,
    TransferenciaCrear, TransferenciaRespuesta, TasaCambioRespuesta,
    ActualizacionTasasRespuesta,
    TarjetaCrear, TarjetaRespuesta, PagoTarjetaCrear, DeteccionCrear, DeteccionConfirmar, DeteccionRespuesta,
    RegistroPropietario, InicioSesion, SolicitudRecuperacion, TokenAccion, RestablecerPassword,
    SesionMovilRespuesta, SesionActivaRespuesta, CodigoMfa, DesactivarMfa, UsuarioRespuesta, UsuarioCrearAdmin, UsuarioActualizarAdmin,
)
from core.database import create_database
from core.config import validar_produccion
from core.ownership import usuario_actual_id
from core.security import limitador_compartido
from core.services import (
    AccountService, AttachmentService, BackupService, BudgetService, CategoryService, DashboardService,
    ExchangeService, GoalService, InvestmentService, MovementService,
    RecurringExpenseService, ReportService, TransferService, CardService, AuthService,
)


ENTORNO = os.getenv("FINANCEOS_ENV", "development").strip().lower()


@asynccontextmanager
async def ciclo_vida(_app: FastAPI):
    validar_produccion()
    create_database()
    yield


app = FastAPI(
    title="FinanceOS API", version="0.1.0",
    description="API local preparada para las aplicaciones web y móvil de FinanceOS.",
    docs_url=None if ENTORNO == "production" else "/docs",
    redoc_url=None if ENTORNO == "production" else "/redoc",
    openapi_url=None if ENTORNO == "production" else "/openapi.json",
    lifespan=ciclo_vida,
)
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
if (FRONTEND_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="frontend-assets")
if (FRONTEND_DIST / "tessdata").is_dir():
    app.mount("/tessdata", StaticFiles(directory=FRONTEND_DIST / "tessdata"), name="ocr-language-data")
ORIGENES_CONFIGURADOS = [origin.strip() for origin in os.getenv("FINANCEOS_CORS_ORIGINS", "").split(",") if origin.strip()]
ORIGENES_DESARROLLO = ["http://localhost:8501", "http://localhost:3000", "http://localhost:5173"] if ENTORNO != "production" else []
ORIGENES_PERMITIDOS = ORIGENES_DESARROLLO + ORIGENES_CONFIGURADOS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENES_PERMITIDOS,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?" if ENTORNO != "production" else None,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
HOSTS_PERMITIDOS = [host.strip() for host in os.getenv(
    "FINANCEOS_ALLOWED_HOSTS", "localhost,127.0.0.1,10.0.2.2,192.168.1.5,testserver"
).split(",") if host.strip()]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=HOSTS_PERMITIDOS)

SOLO_RED_PRIVADA = os.getenv("FINANCEOS_PRIVATE_NETWORK_ONLY", "true").strip().lower() in {"1", "true", "yes", "si"}
AUTH_REQUERIDA = os.getenv("FINANCEOS_AUTH_REQUIRED", "true").strip().lower() in {"1", "true", "yes", "si"}
COOKIE_SESION = "financeos_session"
RUTAS_PUBLICAS = {
    "/api/v1/health", "/api/v1/auth/status", "/api/v1/auth/registro", "/api/v1/auth/login",
    "/api/v1/auth/mobile/login", "/api/v1/auth/recuperacion/solicitar",
    "/api/v1/auth/recuperacion/restablecer", "/api/v1/auth/verificar-correo",
    "/api/v1/auth/verificacion/reenviar",
}

LIMITES_PUBLICOS = {
    "/api/v1/auth/login": (10, 900),
    "/api/v1/auth/mobile/login": (10, 900),
    "/api/v1/auth/registro": (5, 3600),
    "/api/v1/auth/recuperacion/solicitar": (5, 3600),
    "/api/v1/auth/recuperacion/restablecer": (10, 3600),
    "/api/v1/auth/verificar-correo": (10, 3600),
    "/api/v1/auth/verificacion/reenviar": (5, 3600),
}


def _es_origen_de_la_aplicacion(request: Request, origen: str) -> bool:
    """Acepta formularios únicamente desde el mismo host que sirve la interfaz."""
    try:
        origen_url = urlsplit(origen)
    except ValueError:
        return False
    host_solicitud = request.headers.get("host", "").lower()
    return bool(
        origen_url.scheme in {"http", "https"}
        and origen_url.netloc.lower() == host_solicitud
        and origen_url.scheme == request.url.scheme
    )


@app.middleware("http")
async def proteger_api_remota(request: Request, call_next):
    """Aplica red, abuso, origen y sesión antes de ejecutar reglas financieras."""
    cliente = request.client.host if request.client else ""
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.cookies.get(COOKIE_SESION):
        origen = request.headers.get("origin")
        # Los formularios del navegador deben provenir de una interfaz
        # autorizada. Los clientes móviles usan Bearer y no dependen de cookies.
        origen_publico = os.getenv("FINANCEOS_PUBLIC_URL", "").rstrip("/")
        if origen and not _es_origen_de_la_aplicacion(request, origen) and origen not in ORIGENES_PERMITIDOS and origen != origen_publico:
            return Response(content='{"detail":"Origen no autorizado"}', status_code=403, media_type="application/json")
    if request.url.path in LIMITES_PUBLICOS and cliente != "testclient":
        maximo, ventana = LIMITES_PUBLICOS[request.url.path]
        accion = "login" if request.url.path in {"/api/v1/auth/login", "/api/v1/auth/mobile/login"} else request.url.path
        permitido, espera = limitador_compartido.permitir(f"ip:{cliente}:{accion}", maximo, ventana)
        if not permitido:
            return Response(content='{"detail":"Demasiados intentos. Espera antes de continuar."}', status_code=429, media_type="application/json", headers={"Retry-After": str(espera)})
    if SOLO_RED_PRIVADA and cliente:
        try:
            direccion = ip_address(cliente)
        except ValueError:
            # Starlette usa nombres simbólicos en pruebas. En producción se exige
            # siempre una dirección IP real para no abrir accidentalmente la API.
            if ENTORNO == "production":
                return Response(content='{"detail":"Origen no válido"}', status_code=403, media_type="application/json")
            direccion = None
        if direccion and not (direccion.is_private or direccion.is_loopback):
            return Response(content='{"detail":"FinanceOS solo acepta conexiones privadas"}', status_code=403, media_type="application/json")
    contexto_usuario = None
    if AUTH_REQUERIDA and request.url.path.startswith("/api/v1/") and request.url.path not in RUTAS_PUBLICAS:
        service = AuthService()
        try:
            portador = request.headers.get("authorization", "")
            token_sesion = request.cookies.get(COOKIE_SESION)
            if portador.lower().startswith("bearer "):
                token_sesion = portador[7:].strip()
            usuario = service.autenticar(token_sesion)
        finally:
            service.cerrar()
        if usuario is None:
            return Response(content='{"detail":"Sesión requerida"}', status_code=401, media_type="application/json")
        request.state.usuario_id = usuario.id
        contexto_usuario = usuario_actual_id.set(usuario.id)
    try:
        response = await call_next(request)
    finally:
        if contexto_usuario is not None:
            usuario_actual_id.reset(contexto_usuario)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Permissions-Policy"] = "camera=(self), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; connect-src 'self'; font-src 'self' data:; "
        "worker-src 'self' blob:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    )
    if request.url.path.startswith("/api/v1/"):
        response.headers["Cache-Control"] = "no-store"
    if os.getenv("FINANCEOS_HTTPS", "false").strip().lower() in {"1", "true", "yes", "si"}:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


def _error_negocio(error):
    raise HTTPException(status_code=400, detail=str(error)) from error


def _usuario_publico(usuario):
    return {"id": usuario.id, "nombre": usuario.nombre, "correo": usuario.correo, "rol": usuario.rol, "activo": bool(usuario.activo), "mfa_habilitado": bool(usuario.mfa_habilitado)}


def _guardar_cookie(response: Response, token: str):
    response.set_cookie(
        COOKIE_SESION, token, max_age=43200, httponly=True,
        secure=os.getenv("FINANCEOS_HTTPS", "false").lower() == "true",
        samesite="strict", path="/",
    )


def _token_request(request: Request):
    portador = request.headers.get("authorization", "")
    if portador.lower().startswith("bearer "):
        return portador[7:].strip()
    return request.cookies.get(COOKIE_SESION)


@app.get("/", include_in_schema=False)
def inicio():
    """Sirve la interfaz compilada o abre la documentación si aún no existe."""
    index = FRONTEND_DIST / "index.html"
    return FileResponse(index) if index.is_file() else RedirectResponse(url="/docs")


@app.get("/api/v1/health")
def health():
    return {"estado": "ok", "servicio": "financeos-api", "version": app.version}


@app.get("/api/v1/configuracion/seguridad")
def estado_seguridad():
    controles = {
        "sesiones_individuales": AUTH_REQUERIDA,
        "https": os.getenv("FINANCEOS_HTTPS", "false").lower() == "true",
        "postgresql": os.getenv("FINANCEOS_DATABASE_URL", "").startswith("postgresql+"),
        "correo_transaccional": bool(os.getenv("FINANCEOS_SMTP_HOST", "").strip()),
        "registro_publico": os.getenv("FINANCEOS_PUBLIC_SIGNUP", "false").lower() == "true",
        "red_privada": SOLO_RED_PRIVADA,
    }
    esenciales = ["sesiones_individuales", "https", "postgresql", "correo_transaccional"]
    return {"entorno": ENTORNO, "listo_publicacion": all(controles[c] for c in esenciales), "controles": controles}


@app.get("/api/v1/auth/status")
def estado_autenticacion(request: Request):
    service = AuthService()
    try:
        requiere_configuracion = service.requiere_registro()
        registro_publico = service.registro_publico_habilitado()
        usuario = service.autenticar(_token_request(request))
        return {
            "requiere_configuracion": requiere_configuracion,
            "registro_publico": registro_publico,
            "registro_disponible": requiere_configuracion or registro_publico,
            "token_configuracion_requerido": requiere_configuracion and ENTORNO == "production" and not registro_publico,
            "autenticado": usuario is not None,
            "usuario": _usuario_publico(usuario) if usuario else None,
        }
    finally:
        service.cerrar()


@app.post("/api/v1/auth/registro", response_model=UsuarioRespuesta, status_code=201)
def registrar_propietario(datos: RegistroPropietario, response: Response):
    service = AuthService()
    try:
        usuario = service.registrar(datos.nombre, datos.correo, datos.password, datos.token_configuracion)
        if usuario.correo_verificado_en is not None:
            usuario, token = service.iniciar(datos.correo, datos.password)
            _guardar_cookie(response, token)
        return _usuario_publico(usuario)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.post("/api/v1/auth/login", response_model=UsuarioRespuesta)
def iniciar_sesion(datos: InicioSesion, response: Response, request: Request):
    service = AuthService()
    try:
        usuario, token = service.iniciar(datos.correo, datos.password, datos.mfa_codigo, request.headers.get("user-agent", "Navegador web"), request.client.host if request.client else "")
        _guardar_cookie(response, token)
        return _usuario_publico(usuario)
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    finally:
        service.cerrar()


@app.post("/api/v1/auth/mobile/login", response_model=SesionMovilRespuesta)
def iniciar_sesion_movil(datos: InicioSesion, request: Request):
    service = AuthService()
    try:
        usuario, token = service.iniciar(datos.correo, datos.password, datos.mfa_codigo, request.headers.get("user-agent", "Aplicación móvil"), request.client.host if request.client else "")
        return {"usuario": _usuario_publico(usuario), "token": token, "vence_en_segundos": 43200}
    except ValueError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error
    finally:
        service.cerrar()


@app.post("/api/v1/auth/recuperacion/solicitar", status_code=202)
def solicitar_recuperacion(datos: SolicitudRecuperacion):
    service = AuthService()
    try:
        service.solicitar_recuperacion(datos.correo)
        return {"mensaje": "Si la cuenta existe, recibirás instrucciones para continuar."}
    finally:
        service.cerrar()


@app.post("/api/v1/auth/recuperacion/restablecer")
def restablecer_password(datos: RestablecerPassword):
    service = AuthService()
    try:
        service.restablecer_password(datos.token, datos.password)
        return {"mensaje": "Contraseña actualizada. Inicia sesión nuevamente."}
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.post("/api/v1/auth/verificar-correo")
def verificar_correo(datos: TokenAccion):
    service = AuthService()
    try:
        service.verificar_correo(datos.token)
        return {"mensaje": "Correo verificado. Ya puedes iniciar sesión."}
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.post("/api/v1/auth/verificacion/reenviar", status_code=202)
def reenviar_verificacion(datos: SolicitudRecuperacion):
    service = AuthService()
    try:
        service.reenviar_verificacion(datos.correo)
        return {"mensaje": "Si la cuenta está pendiente, enviaremos un enlace nuevo."}
    finally:
        service.cerrar()


@app.post("/api/v1/auth/mfa/preparar")
def preparar_mfa(request: Request):
    service = AuthService()
    try:
        return service.preparar_mfa(request.state.usuario_id)
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.post("/api/v1/auth/mfa/confirmar")
def confirmar_mfa(datos: CodigoMfa, request: Request):
    service = AuthService()
    try:
        service.confirmar_mfa(request.state.usuario_id, datos.codigo)
        return {"mensaje": "Autenticación multifactor activada."}
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.post("/api/v1/auth/mfa/desactivar")
def desactivar_mfa(datos: DesactivarMfa, request: Request):
    service = AuthService()
    try:
        service.desactivar_mfa(request.state.usuario_id, datos.password, datos.codigo)
        return {"mensaje": "Autenticación multifactor desactivada."}
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.post("/api/v1/auth/logout")
def cerrar_sesion(request: Request, response: Response):
    service = AuthService()
    try:
        service.cerrar_sesion(_token_request(request))
    finally:
        service.cerrar()
    response.delete_cookie(COOKIE_SESION, path="/")
    return {"ok": True}


@app.get("/api/v1/auth/sesiones", response_model=list[SesionActivaRespuesta])
def listar_sesiones(request: Request):
    service = AuthService()
    try:
        return [
            {
                "id": sesion.id, "dispositivo": sesion.dispositivo,
                "creada_en": sesion.creada_en, "ultima_actividad": sesion.ultima_actividad,
                "vence_en": sesion.vence_en, "actual": actual,
            }
            for sesion, actual in service.listar_sesiones(request.state.usuario_id, _token_request(request))
        ]
    finally:
        service.cerrar()


@app.delete("/api/v1/auth/sesiones/{sesion_id}", status_code=204, response_class=Response)
def revocar_sesion(sesion_id: int, request: Request):
    service = AuthService()
    try:
        if not service.revocar_sesion(request.state.usuario_id, sesion_id):
            raise HTTPException(status_code=404, detail="La sesión no existe.")
        return Response(status_code=204)
    finally:
        service.cerrar()


@app.get("/api/v1/auth/me", response_model=UsuarioRespuesta)
def usuario_actual(request: Request):
    service = AuthService()
    try:
        usuario = service.autenticar(_token_request(request))
        if usuario is None:
            raise HTTPException(status_code=401, detail="Sesión requerida")
        return _usuario_publico(usuario)
    finally:
        service.cerrar()


@app.get("/api/v1/auth/usuarios", response_model=list[UsuarioRespuesta])
def listar_usuarios(request: Request):
    service = AuthService()
    try:
        return [_usuario_publico(usuario) for usuario in service.listar_usuarios(request.state.usuario_id)]
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    finally:
        service.cerrar()


@app.post("/api/v1/auth/usuarios", response_model=UsuarioRespuesta, status_code=201)
def crear_usuario(datos: UsuarioCrearAdmin, request: Request):
    service = AuthService()
    try:
        usuario = service.crear_usuario(request.state.usuario_id, datos.nombre, datos.correo, datos.password)
        return _usuario_publico(usuario)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.put("/api/v1/auth/usuarios/{usuario_id}", response_model=UsuarioRespuesta)
def actualizar_usuario(usuario_id: int, datos: UsuarioActualizarAdmin, request: Request):
    service = AuthService()
    try:
        usuario = service.actualizar_usuario(request.state.usuario_id, usuario_id, datos.activo)
        return _usuario_publico(usuario)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.get("/api/v1/configuracion/respaldo")
def estado_respaldo(request: Request):
    auth = AuthService()
    try:
        auth.verificar_administrador(request.state.usuario_id)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    finally:
        auth.cerrar()
    service = BackupService()
    estado = service.estado()
    return {
        "motor": estado["motor"],
        "tamano": estado["tamano"],
        "modificado": estado["modificado"].isoformat() if estado["modificado"] else None,
        "disponible": service.disponible,
    }


@app.get("/api/v1/configuracion/respaldo/descargar")
def descargar_respaldo(request: Request):
    auth = AuthService()
    try:
        auth.verificar_administrador(request.state.usuario_id)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    finally:
        auth.cerrar()
    service = BackupService()
    try:
        contenido = service.crear_respaldo()
    except ValueError as error:
        _error_negocio(error)
    return Response(content=contenido, media_type="application/zip", headers={"Content-Disposition": 'attachment; filename="FinanceOS-respaldo.zip"'})


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
            raise HTTPException(status_code=409, detail="La cuenta tiene movimientos o tarjetas vinculadas y no puede eliminarse.")
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


@app.get("/api/v1/tarjetas", response_model=list[TarjetaRespuesta])
def listar_tarjetas():
    service = CardService()
    try:
        return [_serializar_tarjeta(t) for t in service.listar_tarjetas()]
    finally:
        service.cerrar()


@app.post("/api/v1/tarjetas", response_model=TarjetaRespuesta, status_code=201)
def crear_tarjeta(datos: TarjetaCrear):
    service = CardService()
    try:
        return _serializar_tarjeta(service.crear_tarjeta(**datos.model_dump()))
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.delete("/api/v1/tarjetas/{tarjeta_id}", status_code=204, response_class=Response)
def eliminar_tarjeta(tarjeta_id: int):
    service = CardService()
    try:
        if not service.eliminar_tarjeta(tarjeta_id):
            raise HTTPException(status_code=404, detail="La tarjeta no existe.")
        return Response(status_code=204)
    finally:
        service.cerrar()


@app.post("/api/v1/tarjetas/{tarjeta_id}/pagar", response_model=TransferenciaRespuesta)
def pagar_tarjeta(tarjeta_id: int, datos: PagoTarjetaCrear):
    service = CardService()
    try:
        return _serializar_transferencia(service.pagar_tarjeta(tarjeta_id, **datos.model_dump()))
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.get("/api/v1/detecciones", response_model=list[DeteccionRespuesta])
def listar_detecciones(estado: str = "Pendiente"):
    service = CardService()
    try:
        return [_serializar_deteccion(item) for item in service.listar_detecciones(estado)]
    finally:
        service.cerrar()


@app.post("/api/v1/detecciones", response_model=DeteccionRespuesta, status_code=201)
def detectar_operacion(datos: DeteccionCrear):
    service = CardService()
    try:
        operacion, duplicada = service.detectar(**datos.model_dump())
        return _serializar_deteccion(operacion, duplicada)
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.post("/api/v1/detecciones/{operacion_id}/confirmar", response_model=DeteccionRespuesta)
def confirmar_deteccion(operacion_id: int, datos: DeteccionConfirmar):
    service = CardService()
    try:
        operacion = service.confirmar(operacion_id, **datos.model_dump())
        if operacion is None:
            raise HTTPException(status_code=404, detail="La deteccion no existe.")
        return _serializar_deteccion(operacion)
    except ValueError as error:
        _error_negocio(error)
    finally:
        service.cerrar()


@app.post("/api/v1/detecciones/{operacion_id}/descartar", response_model=DeteccionRespuesta)
def descartar_deteccion(operacion_id: int):
    service = CardService()
    try:
        operacion = service.descartar(operacion_id)
        if operacion is None:
            raise HTTPException(status_code=404, detail="La deteccion no existe.")
        return _serializar_deteccion(operacion)
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


@app.get("/api/v1/monedas/tasas", response_model=list[TasaCambioRespuesta])
def listar_tasas():
    service = ExchangeService()
    try:
        return service.obtener_tasas()
    finally:
        service.cerrar()


@app.post("/api/v1/monedas/tasas/actualizar", response_model=ActualizacionTasasRespuesta)
def actualizar_tasas(moneda_base: str = "USD"):
    service = ExchangeService()
    try:
        base = moneda_base.upper()
        if not service.actualizar_tasas(base):
            raise HTTPException(status_code=503, detail="No fue posible consultar las tasas de cambio.")
        tasas = service.obtener_tasas()
        return ActualizacionTasasRespuesta(
            actualizadas=True,
            moneda_base=base,
            ultima_actualizacion=service.ultima_actualizacion(),
            total=len(tasas),
        )
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


@app.get("/api/v1/dashboard/graficas")
def graficas_dashboard():
    service = DashboardService()
    try:
        gastos, pendientes_gastos = service.gastos_por_categoria()
        cuentas, pendientes_cuentas = service.cuentas_por_saldo()
        inversiones, pendientes_inversiones = service.inversiones_por_saldo()
        activos = [item for item in cuentas if item["saldo_cop"] >= 0] + inversiones
        deudas = [{**item, "saldo_cop": abs(item["saldo_cop"])} for item in cuentas if item["saldo_cop"] < 0]
        return {
            "flujo": service.flujo_seis_meses(),
            "gastos_categoria": gastos,
            "distribucion": activos,
            "deudas": deudas,
            "pendientes": len(pendientes_gastos) + len(pendientes_cuentas) + len(pendientes_inversiones),
        }
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


def _serializar_tarjeta(tarjeta):
    return TarjetaRespuesta(id=tarjeta.id, nombre=tarjeta.nombre, banco=tarjeta.banco,
                            ultimos_cuatro=tarjeta.ultimos_cuatro, tipo=tarjeta.tipo,
                            moneda=tarjeta.moneda, cuenta_id=tarjeta.cuenta_id,
                            activa=bool(tarjeta.activa), cuenta=tarjeta.cuenta.nombre,
                            cuenta_tipo=tarjeta.cuenta.tipo, saldo=tarjeta.cuenta.saldo)


def _serializar_deteccion(operacion, duplicada=False):
    return DeteccionRespuesta(id=operacion.id, origen=operacion.origen, comercio=operacion.comercio,
                              valor=operacion.valor, moneda=operacion.moneda, fecha=operacion.fecha,
                              banco=operacion.banco, ultimos_cuatro=operacion.ultimos_cuatro,
                              tipo_sugerido=operacion.tipo_sugerido, estado=operacion.estado,
                              tarjeta_id=operacion.tarjeta_id, movimiento_id=operacion.movimiento_id,
                              duplicada=duplicada)


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
        valores_totales=inversion.valores_totales,
        costo=item["costo"],
        valor=item["valor"],
        ganancia=item["ganancia"],
        rentabilidad=item["rentabilidad"],
        costo_cop=item["costo_base"],
        valor_cop=item["valor_base"],
    )
