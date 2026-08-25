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

from cryptography.fernet import Fernet, InvalidToken


class MfaService:
    def __init__(self):
        clave_archivo = os.getenv("FINANCEOS_MFA_ENCRYPTION_KEY_FILE", "").strip()
        clave = Path(clave_archivo).read_bytes().strip() if clave_archivo else os.getenv("FINANCEOS_MFA_ENCRYPTION_KEY", "").encode()
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
        self.clave_actual_id = os.getenv("FINANCEOS_MFA_CURRENT_KEY_ID", "primary").strip() or "primary"
        self.cifradores = {self.clave_actual_id: Fernet(clave)}
        for entrada in filter(None, (item.strip() for item in os.getenv("FINANCEOS_MFA_PREVIOUS_KEYS", "").split(","))):
            identificador, separador, valor = entrada.partition(":")
            if not separador or not identificador or identificador in self.cifradores:
                raise RuntimeError("FINANCEOS_MFA_PREVIOUS_KEYS debe usar id:clave,id:clave.")
            self.cifradores[identificador] = Fernet(valor.encode())
        self.cifrador = self.cifradores[self.clave_actual_id]

    @staticmethod
    def generar_secreto():
        return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")

    def cifrar(self, secreto: str):
        return f"v1:{self.clave_actual_id}:{self.cifrador.encrypt(secreto.encode()).decode()}"

    def descifrar(self, secreto_cifrado: str):
        if secreto_cifrado.startswith("v1:"):
            _, identificador, token = secreto_cifrado.split(":", 2)
            cifrador = self.cifradores.get(identificador)
            if cifrador is None:
                raise RuntimeError(f"No está disponible la clave MFA '{identificador}'.")
            return cifrador.decrypt(token.encode()).decode()
        for cifrador in self.cifradores.values():
            try:
                return cifrador.decrypt(secreto_cifrado.encode()).decode()
            except InvalidToken:
                continue
        raise RuntimeError("No fue posible descifrar el secreto MFA con las claves configuradas.")

    def necesita_rotacion(self, secreto_cifrado: str):
        return not secreto_cifrado.startswith(f"v1:{self.clave_actual_id}:")

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
        return self.contador_valido(secreto, codigo) is not None

    def contador_valido(self, secreto: str, codigo: str, instante: int | None = None):
        """Devuelve el paso TOTP exacto aceptado para poder consumirlo atómicamente."""
        instante = int(time.time()) if instante is None else instante
        for desfase in (-30, 0, 30):
            instante_candidato = instante + desfase
            if hmac.compare_digest(self.codigo(secreto, instante_candidato), codigo.strip()):
                return instante_candidato // 30
        return None

    @staticmethod
    def uri(secreto: str, correo: str):
        return f"otpauth://totp/FinanceOS:{quote(correo)}?secret={secreto}&issuer=FinanceOS&algorithm=SHA1&digits=6&period=30"
