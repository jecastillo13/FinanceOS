"""Autenticación local segura con Argon2id y sesiones opacas revocables."""

import hashlib
import secrets
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from core.database import get_session
from core.models import SesionUsuario, Usuario


class AuthService:
    DURACION = timedelta(hours=12)
    BLOQUEO = timedelta(minutes=15)
    MAX_INTENTOS = 5
    hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)

    def __init__(self):
        self.db = get_session()

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def requiere_registro(self) -> bool:
        return self.db.query(Usuario.id).first() is None

    def registrar_propietario(self, nombre: str, correo: str, password: str):
        if not self.requiere_registro():
            raise ValueError("FinanceOS ya tiene un propietario registrado.")
        usuario = Usuario(nombre=nombre.strip(), correo=correo.strip().lower(), password_hash=self.hasher.hash(password))
        self.db.add(usuario); self.db.commit(); self.db.refresh(usuario)
        return usuario

    def iniciar(self, correo: str, password: str):
        usuario = self.db.query(Usuario).filter(Usuario.correo == correo.strip().lower()).first()
        ahora = datetime.now()
        if usuario is None:
            # Consume un costo similar para reducir enumeración por tiempo.
            try: self.hasher.verify(self.hasher.hash("contraseña-inválida"), password)
            except VerifyMismatchError: pass
            raise ValueError("Credenciales inválidas.")
        if usuario.bloqueado_hasta and usuario.bloqueado_hasta > ahora:
            raise ValueError("Acceso bloqueado temporalmente. Intenta más tarde.")
        try:
            self.hasher.verify(usuario.password_hash, password)
        except VerifyMismatchError as error:
            usuario.intentos_fallidos += 1
            if usuario.intentos_fallidos >= self.MAX_INTENTOS:
                usuario.bloqueado_hasta = ahora + self.BLOQUEO
                usuario.intentos_fallidos = 0
            self.db.commit()
            raise ValueError("Credenciales inválidas.") from error
        usuario.intentos_fallidos = 0; usuario.bloqueado_hasta = None
        if self.hasher.check_needs_rehash(usuario.password_hash):
            usuario.password_hash = self.hasher.hash(password)
        token = secrets.token_urlsafe(48)
        sesion = SesionUsuario(usuario_id=usuario.id, token_hash=self._hash_token(token), vence_en=ahora + self.DURACION)
        self.db.add(sesion); self.db.commit()
        return usuario, token

    def autenticar(self, token: str | None):
        if not token: return None
        ahora = datetime.now()
        sesion = self.db.query(SesionUsuario).filter(SesionUsuario.token_hash == self._hash_token(token), SesionUsuario.revocada_en.is_(None), SesionUsuario.vence_en > ahora).first()
        if not sesion or not sesion.usuario.activo: return None
        sesion.ultima_actividad = ahora; self.db.commit()
        return sesion.usuario

    def cerrar_sesion(self, token: str | None):
        if not token: return
        sesion = self.db.query(SesionUsuario).filter(SesionUsuario.token_hash == self._hash_token(token)).first()
        if sesion: sesion.revocada_en = datetime.now(); self.db.commit()

    def cerrar(self):
        self.db.close()
