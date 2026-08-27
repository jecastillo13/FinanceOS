"""Validación central de configuración para fallar cerrado en producción."""

import os
from urllib.parse import urlsplit

from cryptography.fernet import Fernet


def _origen_https_valido(valor):
    try:
        url = urlsplit(valor)
    except ValueError:
        return False
    return bool(url.scheme == "https" and url.hostname and not url.username and not url.password and not url.query and not url.fragment)


def validar_produccion():
    if os.getenv("FINANCEOS_ENV", "development").strip().lower() != "production":
        return
    errores = []
    database = os.getenv("FINANCEOS_DATABASE_URL", "")
    if not database.startswith("postgresql+"):
        errores.append("FINANCEOS_DATABASE_URL debe apuntar a PostgreSQL")
    if os.getenv("FINANCEOS_HTTPS", "false").lower() != "true":
        errores.append("FINANCEOS_HTTPS debe ser true")
    if os.getenv("FINANCEOS_AUTH_REQUIRED", "true").lower() != "true":
        errores.append("FINANCEOS_AUTH_REQUIRED debe ser true")
    url_publica = os.getenv("FINANCEOS_PUBLIC_URL", "").rstrip("/")
    if not _origen_https_valido(url_publica):
        errores.append("FINANCEOS_PUBLIC_URL debe usar HTTPS")
    origenes = [item.strip().rstrip("/") for item in os.getenv("FINANCEOS_CORS_ORIGINS", "").split(",") if item.strip()]
    if not origenes or any(not _origen_https_valido(item) or urlsplit(item).path not in {"", "/"} for item in origenes):
        errores.append("FINANCEOS_CORS_ORIGINS debe declarar el origen HTTPS")
    elif url_publica not in origenes:
        errores.append("FINANCEOS_CORS_ORIGINS debe incluir FINANCEOS_PUBLIC_URL")
    if not os.getenv("FINANCEOS_SMTP_HOST", "").strip():
        errores.append("FINANCEOS_SMTP_HOST es obligatorio")
    clave_mfa = os.getenv("FINANCEOS_MFA_ENCRYPTION_KEY", "").strip()
    try:
        Fernet(clave_mfa.encode())
    except (ValueError, TypeError):
        errores.append("FINANCEOS_MFA_ENCRYPTION_KEY es obligatoria")
    try:
        maximo_solicitud = int(os.getenv("FINANCEOS_MAX_REQUEST_BYTES", "12582912"))
        if not 1_048_576 <= maximo_solicitud <= 52_428_800:
            raise ValueError
    except ValueError:
        errores.append("FINANCEOS_MAX_REQUEST_BYTES debe estar entre 1 MB y 50 MB")
    hosts = os.getenv("FINANCEOS_ALLOWED_HOSTS", "")
    if not hosts or "*" in hosts:
        errores.append("FINANCEOS_ALLOWED_HOSTS debe ser explícito")
    if errores:
        raise RuntimeError("Configuración de producción insegura: " + "; ".join(errores))
