from fastapi.testclient import TestClient

from api.main import app
from core.services.attachment_service import AttachmentService
from core.security import LimitadorSolicitudes
from core.config import validar_produccion
import pytest


def test_api_aplica_cabeceras_de_seguridad():
    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["cache-control"] == "no-store"


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
