from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base
from core.services import auth_service
from core.services.auth_service import AuthService
from core.models import Cuenta
from core.ownership import usuario_actual_id
from fastapi.testclient import TestClient
from api.main import app


def test_registro_sesion_y_revocacion(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    monkeypatch.setattr(auth_service, "get_session", session_factory)
    service = AuthService()
    usuario = service.registrar_propietario("Propietario", "dueno@financeos.local", "Una-clave-muy-segura-2026")
    assert usuario.password_hash != "Una-clave-muy-segura-2026"
    assert usuario.password_hash.startswith("$argon2id$")
    usuario_autenticado, token = service.iniciar("dueno@financeos.local", "Una-clave-muy-segura-2026")
    assert usuario_autenticado.id == usuario.id
    assert service.autenticar(token).id == usuario.id
    service.cerrar_sesion(token)
    assert service.autenticar(token) is None
    service.cerrar()


def test_api_exige_sesion_y_logout_la_revoca(monkeypatch):
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
    nuevo = client.post("/api/v1/auth/usuarios", json={"nombre":"Persona dos","correo":"persona2@financeos.local","password":"Otra-clave-muy-segura-2026","rol":"usuario"})
    assert nuevo.status_code == 201
    assert nuevo.json()["rol"] == "usuario"
    assert client.get("/api/v1/auth/usuarios").status_code == 200
    assert client.post("/api/v1/auth/logout").status_code == 200
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.post("/api/v1/auth/login", json={"correo":"persona2@financeos.local","password":"Otra-clave-muy-segura-2026"}).status_code == 200
    assert client.get("/api/v1/auth/usuarios").status_code == 403


def test_usuarios_tienen_datos_aislados_y_admin_gestiona_accesos(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    monkeypatch.setattr(auth_service, "get_session", session_factory)
    auth = AuthService()
    admin = auth.registrar_propietario("Admin", "admin@financeos.local", "Una-clave-muy-segura-2026")
    invitado = auth.crear_usuario(admin.id, "Invitado", "invitado@financeos.local", "Otra-clave-muy-segura-2026")
    assert admin.rol == "administrador"
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
