"""Autenticación local segura con Argon2id y sesiones opacas revocables."""

import hashlib
import os
import secrets
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from core.database import get_session
from core.models import Categoria, SesionUsuario, Usuario
from core.ownership import TABLAS_CON_PROPIETARIO
from core.default_categories import CATEGORIAS_PREDETERMINADAS, COLORES_POR_TIPO
from sqlalchemy import text


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

    def registro_publico_habilitado(self) -> bool:
        return os.getenv("FINANCEOS_PUBLIC_SIGNUP", "false").strip().lower() in {"1", "true", "yes", "si"}

    def _agregar_catalogo(self, usuario_id: int):
        for orden, (tipo, grupo, icono, categoria) in enumerate(CATEGORIAS_PREDETERMINADAS, start=1):
            self.db.add(Categoria(
                nombre=categoria, tipo=tipo, grupo=grupo, icono=icono,
                color=COLORES_POR_TIPO[tipo], es_sistema=1, editable=1,
                activa=1, orden=orden, usuario_id=usuario_id,
            ))

    def _crear_identidad(self, nombre: str, correo: str, password: str, rol: str, crear_catalogo: bool = True):
        correo_limpio = correo.strip().lower()
        if self.db.query(Usuario.id).filter(Usuario.correo == correo_limpio).first():
            raise ValueError("Ya existe un usuario con ese correo.")
        usuario = Usuario(
            nombre=nombre.strip(), correo=correo_limpio,
            password_hash=self.hasher.hash(password), rol=rol,
        )
        self.db.add(usuario); self.db.flush()
        if crear_catalogo:
            self._agregar_catalogo(usuario.id)
        return usuario

    def registrar(self, nombre: str, correo: str, password: str):
        configuracion_inicial = self.requiere_registro()
        if not configuracion_inicial and not self.registro_publico_habilitado():
            raise ValueError("El registro público no está habilitado.")
        rol = "usuario" if self.registro_publico_habilitado() else "superadmin"
        usuario = self._crear_identidad(
            nombre, correo, password, rol,
            crear_catalogo=not (configuracion_inicial and rol == "superadmin"),
        )
        if configuracion_inicial and rol == "superadmin":
            # Una instalación local anterior conserva sus registros y los
            # vincula al administrador que completa la configuración inicial.
            for tabla in TABLAS_CON_PROPIETARIO:
                self.db.execute(text(f"UPDATE {tabla} SET usuario_id = :id WHERE usuario_id IS NULL"), {"id": usuario.id})
            if self.db.query(Categoria.id).filter(Categoria.usuario_id == usuario.id).first() is None:
                self._agregar_catalogo(usuario.id)
        self.db.commit(); self.db.refresh(usuario)
        return usuario

    def registrar_propietario(self, nombre: str, correo: str, password: str):
        """Compatibilidad con clientes anteriores; respeta el modo configurado."""
        return self.registrar(nombre, correo, password)

    def crear_superadmin(self, nombre: str, correo: str, password: str):
        usuario = self._crear_identidad(nombre, correo, password, "superadmin")
        self.db.commit(); self.db.refresh(usuario)
        return usuario

    def _administrador(self, usuario_id: int):
        usuario = self.db.get(Usuario, usuario_id)
        if usuario is None or not usuario.activo or usuario.rol != "superadmin":
            raise PermissionError("Solo un superadministrador puede gestionar usuarios.")
        return usuario

    def listar_usuarios(self, solicitante_id: int):
        self._administrador(solicitante_id)
        return self.db.query(Usuario).order_by(Usuario.creado_en, Usuario.id).all()

    def verificar_administrador(self, usuario_id: int):
        self._administrador(usuario_id)

    def crear_usuario(self, solicitante_id: int, nombre: str, correo: str, password: str):
        self._administrador(solicitante_id)
        usuario = self._crear_identidad(nombre, correo, password, "usuario")
        self.db.commit(); self.db.refresh(usuario)
        return usuario

    def actualizar_usuario(self, solicitante_id: int, usuario_id: int, activo: bool):
        administrador = self._administrador(solicitante_id)
        usuario = self.db.get(Usuario, usuario_id)
        if usuario is None:
            raise ValueError("El usuario no existe.")
        if usuario.id == administrador.id and not activo:
            raise ValueError("No puedes desactivar tu propio acceso de superadministrador.")
        if usuario.rol == "superadmin" and not activo:
            otros = self.db.query(Usuario.id).filter(
                Usuario.rol == "superadmin", Usuario.activo == 1, Usuario.id != usuario.id,
            ).first()
            if otros is None:
                raise ValueError("FinanceOS debe conservar al menos un superadministrador activo.")
        usuario.activo = int(activo)
        if not activo:
            ahora = datetime.now()
            self.db.query(SesionUsuario).filter(
                SesionUsuario.usuario_id == usuario.id, SesionUsuario.revocada_en.is_(None),
            ).update({SesionUsuario.revocada_en: ahora}, synchronize_session=False)
        self.db.commit(); self.db.refresh(usuario)
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
