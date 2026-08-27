from fastapi.testclient import TestClient

from api.main import app
from core.services.attachment_service import AttachmentService
from core.security import LimitadorSolicitudes
from core.config import validar_produccion
from cryptography.fernet import Fernet
import pytest


def test_api_aplica_cabeceras_de_seguridad():
    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["cross-origin-opener-policy"] == "same-origin"
    assert response.headers["cross-origin-resource-policy"] == "same-origin"
    assert response.headers["x-request-id"]
    assert response.headers["cache-control"] == "no-store"


def test_proteccion_de_origen_acepta_la_propia_aplicacion_y_rechaza_terceros():
    cliente = TestClient(app)
    cliente.cookies.set("financeos_session", "sesion-invalida")

    mismo_origen = cliente.post(
        "/ruta-de-prueba-inexistente",
        headers={"Origin": "http://testserver"},
    )
    origen_externo = cliente.post(
        "/ruta-de-prueba-inexistente",
        headers={"Origin": "https://sitio-malicioso.example"},
    )

    assert mismo_origen.status_code == 404
    assert origen_externo.status_code == 403
    assert origen_externo.json()["detail"] == "Origen no autorizado"
    assert origen_externo.headers["x-frame-options"] == "DENY"
    assert origen_externo.headers["x-request-id"]


def test_api_limita_solicitudes_antes_de_procesarlas_y_conserva_correlacion():
    cliente = TestClient(app)
    response = cliente.post(
        "/api/v1/auth/login",
        content=b"{}",
        headers={"Content-Length": str(13 * 1024 * 1024), "X-Request-ID": "prueba-segura-123"},
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "La solicitud supera el límite permitido"
    assert response.headers["x-request-id"] == "prueba-segura-123"
    assert response.headers["x-content-type-options"] == "nosniff"


def test_api_reemplaza_identificador_de_correlacion_malicioso():
    response = TestClient(app).get(
        "/api/v1/health", headers={"X-Request-ID": "valor\r\ninvalido"}
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] != "valor\r\ninvalido"
    assert len(response.headers["x-request-id"]) == 32


def test_firmas_de_comprobantes_rechazan_contenido_disfrazado():
    assert AttachmentService.FIRMAS_VALIDAS["application/pdf"](b"%PDF-1.7\n")
    assert AttachmentService.FIRMAS_VALIDAS["image/png"](b"\x89PNG\r\n\x1a\nresto")
    assert not AttachmentService.FIRMAS_VALIDAS["application/pdf"](b"programa.exe")
    assert not AttachmentService.FIRMAS_VALIDAS["image/jpeg"](b"texto que no es una imagen")


def test_limitador_bloquea_abuso_sin_afectar_otras_claves():
    limitador = LimitadorSolicitudes()
    assert limitador.permitir("ip-a:login", 2, 60)[0]
    assert limitador.permitir("ip-a:login", 2, 60)[0]
    permitido, espera = limitador.permitir("ip-a:login", 2, 60)
    assert not permitido and espera > 0
    assert limitador.permitir("ip-b:login", 2, 60)[0]


def test_produccion_falla_cerrada_si_faltan_controles(monkeypatch):
    monkeypatch.setenv("FINANCEOS_ENV", "production")
    monkeypatch.setenv("FINANCEOS_DATABASE_URL", "sqlite:///insegura.db")
    monkeypatch.delenv("FINANCEOS_SMTP_HOST", raising=False)
    monkeypatch.delenv("FINANCEOS_MFA_ENCRYPTION_KEY", raising=False)
    with pytest.raises(RuntimeError, match="Configuración de producción insegura"):
        validar_produccion()


def test_produccion_acepta_configuracion_coherente(monkeypatch):
    monkeypatch.setenv("FINANCEOS_ENV", "production")
    monkeypatch.setenv("FINANCEOS_DATABASE_URL", "postgresql+psycopg://financeos:clave@database/financeos")
    monkeypatch.setenv("FINANCEOS_HTTPS", "true")
    monkeypatch.setenv("FINANCEOS_AUTH_REQUIRED", "true")
    monkeypatch.setenv("FINANCEOS_PUBLIC_URL", "https://financeos.example.com")
    monkeypatch.setenv("FINANCEOS_CORS_ORIGINS", "https://financeos.example.com")
    monkeypatch.setenv("FINANCEOS_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("FINANCEOS_MFA_ENCRYPTION_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("FINANCEOS_ALLOWED_HOSTS", "financeos.example.com")
    monkeypatch.setenv("FINANCEOS_MAX_REQUEST_BYTES", "12582912")

    validar_produccion()


def test_produccion_rechaza_origen_con_ruta_y_clave_mfa_invalida(monkeypatch):
    monkeypatch.setenv("FINANCEOS_ENV", "production")
    monkeypatch.setenv("FINANCEOS_DATABASE_URL", "postgresql+psycopg://financeos:clave@database/financeos")
    monkeypatch.setenv("FINANCEOS_HTTPS", "true")
    monkeypatch.setenv("FINANCEOS_AUTH_REQUIRED", "true")
    monkeypatch.setenv("FINANCEOS_PUBLIC_URL", "https://financeos.example.com")
    monkeypatch.setenv("FINANCEOS_CORS_ORIGINS", "https://financeos.example.com/ruta")
    monkeypatch.setenv("FINANCEOS_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("FINANCEOS_MFA_ENCRYPTION_KEY", "no-es-una-clave-fernet")
    monkeypatch.setenv("FINANCEOS_ALLOWED_HOSTS", "financeos.example.com")

    with pytest.raises(RuntimeError, match="CORS|MFA"):
        validar_produccion()
