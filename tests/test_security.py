from fastapi.testclient import TestClient

from api.main import app
from core.services.attachment_service import AttachmentService


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
