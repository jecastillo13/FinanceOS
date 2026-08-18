"""Validación central de configuración para fallar cerrado en producción."""

import os


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
    if not os.getenv("FINANCEOS_PUBLIC_URL", "").startswith("https://"):
        errores.append("FINANCEOS_PUBLIC_URL debe usar HTTPS")
    if not os.getenv("FINANCEOS_CORS_ORIGINS", "").startswith("https://"):
        errores.append("FINANCEOS_CORS_ORIGINS debe declarar el origen HTTPS")
    if not os.getenv("FINANCEOS_SMTP_HOST", "").strip():
        errores.append("FINANCEOS_SMTP_HOST es obligatorio")
    if not os.getenv("FINANCEOS_MFA_ENCRYPTION_KEY", "").strip():
        errores.append("FINANCEOS_MFA_ENCRYPTION_KEY es obligatoria")
    hosts = os.getenv("FINANCEOS_ALLOWED_HOSTS", "")
    if not hosts or "*" in hosts:
        errores.append("FINANCEOS_ALLOWED_HOSTS debe ser explícito")
    if errores:
        raise RuntimeError("Configuración de producción insegura: " + "; ".join(errores))
