"""TOTP compatible con RFC 6238 y secretos cifrados en reposo."""

import base64
import hashlib
import hmac
import os
import secrets
import struct
import time
from pathlib import Path
from urllib.parse import quote

from cryptography.fernet import Fernet


class MfaService:
    def __init__(self):
        clave = os.getenv("FINANCEOS_MFA_ENCRYPTION_KEY", "").encode()
        if not clave:
            if os.getenv("FINANCEOS_ENV", "development").lower() == "production":
                raise RuntimeError("FINANCEOS_MFA_ENCRYPTION_KEY es obligatoria en producción")
            ruta = Path(__file__).resolve().parents[2] / "database" / ".mfa_key"
            if ruta.exists():
                clave = ruta.read_bytes().strip()
            else:
                clave = Fernet.generate_key()
                ruta.parent.mkdir(parents=True, exist_ok=True)
                ruta.write_bytes(clave)
        self.cifrador = Fernet(clave)

    @staticmethod
    def generar_secreto():
        return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")

    def cifrar(self, secreto: str):
        return self.cifrador.encrypt(secreto.encode()).decode()

    def descifrar(self, secreto_cifrado: str):
        return self.cifrador.decrypt(secreto_cifrado.encode()).decode()

    @staticmethod
    def codigo(secreto: str, instante: int | None = None):
        instante = instante or int(time.time())
        contador = instante // 30
        relleno = secreto + "=" * ((8 - len(secreto) % 8) % 8)
        clave = base64.b32decode(relleno, casefold=True)
        digest = hmac.new(clave, struct.pack(">Q", contador), hashlib.sha1).digest()
        offset = digest[-1] & 0x0F
        numero = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
        return f"{numero:06d}"

    def verificar(self, secreto: str, codigo: str):
        actual = int(time.time())
        return any(hmac.compare_digest(self.codigo(secreto, actual + desfase), codigo.strip()) for desfase in (-30, 0, 30))

    @staticmethod
    def uri(secreto: str, correo: str):
        return f"otpauth://totp/FinanceOS:{quote(correo)}?secret={secreto}&issuer=FinanceOS&algorithm=SHA1&digits=6&period=30"
