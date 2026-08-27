from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest
from cryptography.fernet import Fernet

from core.database import Base
from core.services import auth_service
from core.services.auth_service import AuthService
from core.services.mfa_service import MfaService
from core.models import Cuenta
from core.ownership import usuario_actual_id
from fastapi.testclient import TestClient
from api.main import app


def test_registro_sesion_y_revocacion(monkeypatch):
    monkeypatch.setenv("FINANCEOS_PUBLIC_SIGNUP", "false")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    monkeypatch.setattr(auth_service, "get_session", session_factory)
    service = AuthService()
    usuario = service.registrar_propietario("Propietario", "dueno@financeos.local", "Una-clave-muy-segura-2026")
    assert usuario.password_hash != "Una-clave-muy-segura-2026"
    assert usuario.password_hash.startswith("$argon2id$")
    assert usuario.rol == "superadmin"
    usuario_autenticado, token = service.iniciar("dueno@financeos.local", "Una-clave-muy-segura-2026")
    assert usuario_autenticado.id == usuario.id
    assert service.autenticar(token).id == usuario.id
    service.cerrar_sesion(token)
    assert service.autenticar(token) is None
    service.cerrar()


def test_api_exige_sesion_y_logout_la_revoca(monkeypatch):
    monkeypatch.setenv("FINANCEOS_PUBLIC_SIGNUP", "false")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    monkeypatch.setattr(auth_service, "get_session", session_factory)
    client = TestClient(app)

    assert client.get("/api/v1/auth/me").status_code == 401
    registro = client.post("/api/v1/auth/registro", json={"nombre":"Propietario","correo":"dueno@financeos.local","password":"Una-clave-muy-segura-2026"})
    assert registro.status_code == 201
    assert registro.cookies.get("financeos_session")
    assert client.get("/api/v1/auth/me").status_code == 200
    nuevo = client.post("/api/v1/auth/usuarios", json={"nombre":"Persona dos","correo":"persona2@financeos.local","password":"Otra-clave-muy-segura-2026"})
    assert nuevo.status_code == 201
    assert nuevo.json()["rol"] == "usuario"
    assert client.get("/api/v1/auth/usuarios").status_code == 200
    assert client.post("/api/v1/auth/logout").status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.post("/api/v1/auth/login", json={"correo":"persona2@financeos.local","password":"Otra-clave-muy-segura-2026"}).status_code == 200
    assert client.get("/api/v1/auth/usuarios").status_code == 403


def test_usuarios_tienen_datos_aislados_y_admin_gestiona_accesos(monkeypatch):
    monkeypatch.setenv("FINANCEOS_PUBLIC_SIGNUP", "false")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    monkeypatch.setattr(auth_service, "get_session", session_factory)
    auth = AuthService()
    admin = auth.registrar_propietario("Admin", "admin@financeos.local", "Una-clave-muy-segura-2026")
    invitado = auth.crear_usuario(admin.id, "Invitado", "invitado@financeos.local", "Otra-clave-muy-segura-2026")
    assert admin.rol == "superadmin"
    assert invitado.rol == "usuario"

    db = session_factory()
    contexto_admin = usuario_actual_id.set(admin.id)
    cuenta_admin = Cuenta(nombre="Cuenta privada A", tipo="Ahorros", saldo=100, moneda="COP")
    db.add(cuenta_admin); db.commit(); admin_cuenta_id = cuenta_admin.id
    usuario_actual_id.reset(contexto_admin)

    contexto_invitado = usuario_actual_id.set(invitado.id)
    cuenta_invitado = Cuenta(nombre="Cuenta privada B", tipo="Ahorros", saldo=200, moneda="COP")
    db.add(cuenta_invitado); db.commit()
    db.close()
    db = session_factory()
    assert [cuenta.nombre for cuenta in db.query(Cuenta).all()] == ["Cuenta privada B"]
    assert db.get(Cuenta, admin_cuenta_id) is None
    usuario_actual_id.reset(contexto_invitado)
    db.close(); auth.cerrar()


def test_registro_publico_nunca_otorga_privilegios(monkeypatch):
    monkeypatch.setenv("FINANCEOS_PUBLIC_SIGNUP", "true")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    monkeypatch.setattr(auth_service, "get_session", session_factory)
    service = AuthService()
    primero = service.registrar("Primero", "primero@financeos.local", "Una-clave-muy-segura-2026")
    segundo = service.registrar("Segundo", "segundo@financeos.local", "Otra-clave-muy-segura-2026")
    assert primero.rol == segundo.rol == "usuario"
    try:
        service.listar_usuarios(primero.id)
        assert False, "Un usuario normal no debe administrar la plataforma"
    except PermissionError:
        pass
    superadmin = service.crear_superadmin("Operaciones", "ops@financeos.local", "Clave-operaciones-segura-2026")
    assert superadmin.rol == "superadmin"
    assert len(service.listar_usuarios(superadmin.id)) == 3
    service.cerrar()


def test_verificacion_y_recuperacion_son_de_un_solo_uso(monkeypatch):
    monkeypatch.setenv("FINANCEOS_PUBLIC_SIGNUP", "true")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    monkeypatch.setattr(auth_service, "get_session", session_factory)
    enviados = []
    monkeypatch.setattr("core.services.email_service.EmailService.enviar_verificacion", lambda self, correo, token: enviados.append(("verificar", token)))
    monkeypatch.setattr("core.services.email_service.EmailService.enviar_recuperacion", lambda self, correo, token: enviados.append(("recuperar", token)))
    service = AuthService()
    usuario = service.registrar("Persona", "persona@financeos.local", "Clave-Publica-Segura-2026")
    assert usuario.correo_verificado_en is None
    with pytest.raises(ValueError, match="verificar"):
        service.iniciar(usuario.correo, "Clave-Publica-Segura-2026")
    service.verificar_correo(enviados.pop()[1])
    _, sesion = service.iniciar(usuario.correo, "Clave-Publica-Segura-2026")
    service.solicitar_recuperacion(usuario.correo)
    token_recuperacion = enviados.pop()[1]
    service.restablecer_password(token_recuperacion, "Clave-Nueva-Segura-2027")
    assert service.autenticar(sesion) is None
    with pytest.raises(ValueError, match="válido"):
        service.restablecer_password(token_recuperacion, "Otra-Clave-Segura-2028")
    service.cerrar()


def test_mfa_exige_codigo_temporal_y_cifra_el_secreto(monkeypatch):
    monkeypatch.setenv("FINANCEOS_PUBLIC_SIGNUP", "false")
    monkeypatch.setenv("FINANCEOS_MFA_ENCRYPTION_KEY", Fernet.generate_key().decode())
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    monkeypatch.setattr(auth_service, "get_session", session_factory)
    service = AuthService()
    usuario = service.registrar("Propietario", "mfa@financeos.local", "Clave-Mfa-Segura-2026")
    preparacion = service.preparar_mfa(usuario.id)
    assert preparacion["secreto"] not in service.db.get(type(usuario), usuario.id).mfa_secret_encrypted
    instante = __import__("time").time_ns() // 1_000_000_000
    monkeypatch.setattr("core.services.mfa_service.time.time", lambda: instante)
    codigo = MfaService.codigo(preparacion["secreto"], instante)
    service.confirmar_mfa(usuario.id, codigo)
    with pytest.raises(ValueError, match="MFA_REQUIRED"):
        service.iniciar(usuario.correo, "Clave-Mfa-Segura-2026")
    with pytest.raises(ValueError, match="ya fue utilizado"):
        service.iniciar(usuario.correo, "Clave-Mfa-Segura-2026", codigo)
    siguiente_instante = instante + 30
    monkeypatch.setattr("core.services.mfa_service.time.time", lambda: siguiente_instante)
    codigo_siguiente = MfaService.codigo(preparacion["secreto"], siguiente_instante)
    autenticado, _ = service.iniciar(usuario.correo, "Clave-Mfa-Segura-2026", codigo_siguiente)
    assert autenticado.id == usuario.id
    with pytest.raises(ValueError, match="ya fue utilizado"):
        service.desactivar_mfa(usuario.id, "Clave-Mfa-Segura-2026", codigo_siguiente)
    ultimo_instante = instante + 60
    monkeypatch.setattr("core.services.mfa_service.time.time", lambda: ultimo_instante)
    service.desactivar_mfa(
        usuario.id,
        "Clave-Mfa-Segura-2026",
        MfaService.codigo(preparacion["secreto"], ultimo_instante),
    )
    service.cerrar()


def test_produccion_exige_aprovisionamiento_local_del_primer_superadmin(monkeypatch):
    monkeypatch.setenv("FINANCEOS_ENV", "production")
    monkeypatch.setenv("FINANCEOS_PUBLIC_SIGNUP", "false")
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    monkeypatch.setattr(auth_service, "get_session", session_factory)
    service = AuthService()
    with pytest.raises(PermissionError, match="create_superadmin.py"):
        service.registrar("Intruso", "intruso@financeos.local", "Clave-Intruso-Segura-2026")
    administrador = service.crear_superadmin("Administrador", "admin@financeos.local", "Clave-Administrador-Segura-2026")
    assert administrador.rol == "superadmin"
    service.cerrar()


def test_mfa_activo_no_puede_reemplazarse_sin_desactivarlo(monkeypatch):
    monkeypatch.setenv("FINANCEOS_ENV", "development")
    monkeypatch.setenv("FINANCEOS_PUBLIC_SIGNUP", "false")
    monkeypatch.setenv("FINANCEOS_MFA_ENCRYPTION_KEY", Fernet.generate_key().decode())
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    monkeypatch.setattr(auth_service, "get_session", session_factory)
    service = AuthService()
    usuario = service.registrar("Propietario", "mfa2@financeos.local", "Clave-Mfa-Segura-2026")
    preparacion = service.preparar_mfa(usuario.id)
    service.confirmar_mfa(usuario.id, MfaService.codigo(preparacion["secreto"]))
    secreto_cifrado = service.db.get(type(usuario), usuario.id).mfa_secret_encrypted
    with pytest.raises(ValueError, match="MFA ya está activo"):
        service.preparar_mfa(usuario.id)
    assert service.db.get(type(usuario), usuario.id).mfa_secret_encrypted == secreto_cifrado
    service.cerrar()
