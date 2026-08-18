from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base
from core.services import auth_service
from core.services.auth_service import AuthService
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

    assert client.get("/api/v1/cuentas").status_code == 401
    registro = client.post("/api/v1/auth/registro", json={"nombre":"Propietario","correo":"dueno@financeos.local","password":"Una-clave-muy-segura-2026"})
    assert registro.status_code == 201
    assert registro.cookies.get("financeos_session")
    assert client.get("/api/v1/cuentas").status_code == 200
    assert client.post("/api/v1/auth/logout").status_code == 200
    assert client.get("/api/v1/cuentas").status_code == 401
