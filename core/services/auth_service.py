"""Autenticación local segura con Argon2id y sesiones opacas revocables."""

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from core.database import get_session
from core.models import Categoria, SesionUsuario, TokenSeguridadUsuario, Usuario
from core.services.email_service import EmailService
from core.services.mfa_service import MfaService
from core.ownership import TABLAS_CON_PROPIETARIO
from core.default_categories import CATEGORIAS_PREDETERMINADAS, COLORES_POR_TIPO
from sqlalchemy import or_, text, update

logger = logging.getLogger(__name__)


class AuthService:
    DURACION = timedelta(hours=12)
    INACTIVIDAD_MAXIMA = timedelta(minutes=30)
    MAX_INTENTOS_MFA = 5
    BLOQUEO = timedelta(minutes=15)
    MAX_INTENTOS = 5
    hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
    HASH_SIMULADO = hasher.hash("contraseña-inválida")

    def __init__(self):
        self.db = get_session()

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def requiere_registro(self) -> bool:
        return self.db.query(Usuario.id).first() is None

    def registro_publico_habilitado(self) -> bool:
        entorno = os.getenv("FINANCEOS_ENV", "development").strip().lower()
        predeterminado = "true" if entorno == "development" else "false"
        return os.getenv("FINANCEOS_PUBLIC_SIGNUP", predeterminado).strip().lower() in {"1", "true", "yes", "si"}

    def _agregar_catalogo(self, usuario_id: int):
        for orden, (tipo, grupo, icono, categoria) in enumerate(CATEGORIAS_PREDETERMINADAS, start=1):
            self.db.add(Categoria(
                nombre=categoria, tipo=tipo, grupo=grupo, icono=icono,
                color=COLORES_POR_TIPO[tipo], es_sistema=1, editable=1,
                activa=1, orden=orden, usuario_id=usuario_id,
            ))

    @staticmethod
    def _validar_password(password: str):
        if len(password) < 12 or len(password) > 128:
            raise ValueError("La contraseña debe tener entre 12 y 128 caracteres.")
        if password.lower() == password or password.upper() == password or not any(c.isdigit() for c in password):
            raise ValueError("Usa mayúsculas, minúsculas y al menos un número.")

    def _crear_token_seguridad(self, usuario_id: int, proposito: str, duracion: timedelta):
        ahora = datetime.now()
        self.db.query(TokenSeguridadUsuario).filter(
            TokenSeguridadUsuario.usuario_id == usuario_id,
            TokenSeguridadUsuario.proposito == proposito,
            TokenSeguridadUsuario.usado_en.is_(None),
        ).update({TokenSeguridadUsuario.usado_en: ahora}, synchronize_session=False)
        token = secrets.token_urlsafe(48)
        self.db.add(TokenSeguridadUsuario(
            usuario_id=usuario_id, proposito=proposito,
            token_hash=self._hash_token(token), vence_en=ahora + duracion,
        ))
        return token

    def _reclamar_codigo_mfa(self, usuario: Usuario, secreto: str, codigo: str):
        """Valida y consume un paso TOTP una sola vez en cualquier operación sensible."""
        contador = MfaService().contador_valido(secreto, codigo)
        if contador is None:
            raise ValueError("El código de verificación no es válido.")
        reclamado = self.db.execute(
            update(Usuario)
            .where(
                Usuario.id == usuario.id,
                or_(
                    Usuario.mfa_ultimo_contador_usado.is_(None),
                    Usuario.mfa_ultimo_contador_usado < contador,
                ),
            )
            .values(mfa_ultimo_contador_usado=contador)
        )
        if reclamado.rowcount != 1:
            self.db.rollback()
            raise ValueError("El código de verificación ya fue utilizado.")
        return contador

    def _crear_identidad(self, nombre: str, correo: str, password: str, rol: str, crear_catalogo: bool = True):
        self._validar_password(password)
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
        if configuracion_inicial and os.getenv("FINANCEOS_ENV", "development").strip().lower() == "production":
            raise PermissionError("El primer administrador de producción debe crearse localmente con scripts/create_superadmin.py.")
        rol = "superadmin" if configuracion_inicial else "usuario"
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
            usuario.correo_verificado_en = datetime.now()
        if rol == "usuario" and self.registro_publico_habilitado():
            if os.getenv("FINANCEOS_ENV", "development").strip().lower() == "development" and not os.getenv("FINANCEOS_SMTP_HOST", "").strip():
                usuario.correo_verificado_en = datetime.now()
                self.db.commit(); self.db.refresh(usuario)
                return usuario
            token = self._crear_token_seguridad(usuario.id, "verificar_correo", timedelta(hours=24))
            self.db.commit(); self.db.refresh(usuario)
            try:
                EmailService().enviar_verificacion(usuario.correo, token)
            except Exception:
                logger.exception("No fue posible entregar el correo de verificación")
            return usuario
        usuario.correo_verificado_en = usuario.correo_verificado_en or datetime.now()
        self.db.commit(); self.db.refresh(usuario)
        return usuario

    def registrar_propietario(self, nombre: str, correo: str, password: str):
        """Compatibilidad con clientes anteriores; respeta el modo configurado."""
        return self.registrar(nombre, correo, password)

    def crear_superadmin(self, nombre: str, correo: str, password: str):
        usuario = self._crear_identidad(nombre, correo, password, "superadmin")
        usuario.correo_verificado_en = datetime.now()
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
        usuario.correo_verificado_en = datetime.now()
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

    def iniciar(self, correo: str, password: str, mfa_codigo: str | None = None, dispositivo: str = "Dispositivo desconocido", ip: str = ""):
        consulta = self.db.query(Usuario).filter(Usuario.correo == correo.strip().lower())
        if self.db.bind.dialect.name != "sqlite":
            consulta = consulta.with_for_update()
        usuario = consulta.first()
        ahora = datetime.now()
        if usuario is None:
            # Consume un costo similar para reducir enumeración por tiempo.
            try: self.hasher.verify(self.HASH_SIMULADO, password)
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
        if usuario.correo_verificado_en is None:
            raise ValueError("Debes verificar tu correo antes de iniciar sesión.")
        if usuario.mfa_habilitado:
            if not mfa_codigo:
                raise ValueError("MFA_REQUIRED")
            mfa = MfaService()
            secreto = mfa.descifrar(usuario.mfa_secret_encrypted)
            if mfa.necesita_rotacion(usuario.mfa_secret_encrypted):
                usuario.mfa_secret_encrypted = mfa.cifrar(secreto)
            try:
                self._reclamar_codigo_mfa(usuario, secreto, mfa_codigo)
            except ValueError as error:
                usuario.intentos_fallidos += 1
                if usuario.intentos_fallidos >= self.MAX_INTENTOS_MFA:
                    usuario.bloqueado_hasta = ahora + self.BLOQUEO
                    usuario.intentos_fallidos = 0
                self.db.commit()
                raise error
        usuario.intentos_fallidos = 0; usuario.bloqueado_hasta = None
        if self.hasher.check_needs_rehash(usuario.password_hash):
            usuario.password_hash = self.hasher.hash(password)
        token = secrets.token_urlsafe(48)
        sesion = SesionUsuario(
            usuario_id=usuario.id,
            token_hash=self._hash_token(token),
            vence_en=ahora + self.DURACION,
            dispositivo=str(dispositivo or "Dispositivo desconocido")[:160],
            ip_hash=self._hash_token(ip) if ip else None,
        )
        self.db.add(sesion); self.db.commit()
        return usuario, token

    def preparar_mfa(self, usuario_id: int):
        usuario = self.db.get(Usuario, usuario_id)
        if not usuario or not usuario.activo:
            raise ValueError("El usuario no existe.")
        if usuario.mfa_habilitado:
            raise ValueError("MFA ya está activo. Desactívalo con tu contraseña y código actual antes de configurarlo nuevamente.")
        secreto = MfaService.generar_secreto()
        usuario.mfa_secret_encrypted = MfaService().cifrar(secreto)
        usuario.mfa_habilitado = 0
        usuario.mfa_ultimo_contador_usado = None
        self.db.commit()
        return {"secreto": secreto, "uri": MfaService.uri(secreto, usuario.correo)}

    def confirmar_mfa(self, usuario_id: int, codigo: str):
        usuario = self.db.get(Usuario, usuario_id)
        if not usuario or not usuario.mfa_secret_encrypted:
            raise ValueError("Primero inicia la configuración de MFA.")
        servicio = MfaService()
        self._reclamar_codigo_mfa(usuario, servicio.descifrar(usuario.mfa_secret_encrypted), codigo)
        usuario.mfa_habilitado = 1
        self.db.commit()

    def desactivar_mfa(self, usuario_id: int, password: str, codigo: str):
        usuario = self.db.get(Usuario, usuario_id)
        if not usuario or not usuario.mfa_habilitado:
            raise ValueError("MFA no está activo.")
        try:
            self.hasher.verify(usuario.password_hash, password)
        except VerifyMismatchError as error:
            raise ValueError("Credenciales inválidas.") from error
        servicio = MfaService()
        self._reclamar_codigo_mfa(usuario, servicio.descifrar(usuario.mfa_secret_encrypted), codigo)
        usuario.mfa_habilitado = 0
        usuario.mfa_secret_encrypted = None
        usuario.mfa_ultimo_contador_usado = None
        self.db.commit()

    def solicitar_recuperacion(self, correo: str):
        usuario = self.db.query(Usuario).filter(Usuario.correo == correo.strip().lower(), Usuario.activo == 1).first()
        if usuario:
            token = self._crear_token_seguridad(usuario.id, "recuperar_password", timedelta(minutes=30))
            self.db.commit()
            try:
                return EmailService().enviar_recuperacion(usuario.correo, token)
            except Exception:
                logger.exception("No fue posible entregar el correo de recuperación")
        return None

    def reenviar_verificacion(self, correo: str):
        usuario = self.db.query(Usuario).filter(Usuario.correo == correo.strip().lower(), Usuario.activo == 1).first()
        if usuario and usuario.correo_verificado_en is None:
            token = self._crear_token_seguridad(usuario.id, "verificar_correo", timedelta(hours=24))
            self.db.commit()
            try:
                EmailService().enviar_verificacion(usuario.correo, token)
            except Exception:
                logger.exception("No fue posible reenviar el correo de verificación")

    def verificar_correo(self, token: str):
        registro = self._token_valido(token, "verificar_correo")
        registro.usuario.correo_verificado_en = datetime.now()
        registro.usado_en = datetime.now()
        self.db.commit()

    def restablecer_password(self, token: str, password: str):
        self._validar_password(password)
        registro = self._token_valido(token, "recuperar_password")
        ahora = datetime.now()
        registro.usuario.password_hash = self.hasher.hash(password)
        registro.usuario.intentos_fallidos = 0
        registro.usuario.bloqueado_hasta = None
        registro.usado_en = ahora
        self.db.query(SesionUsuario).filter(
            SesionUsuario.usuario_id == registro.usuario_id,
            SesionUsuario.revocada_en.is_(None),
        ).update({SesionUsuario.revocada_en: ahora}, synchronize_session=False)
        self.db.commit()

    def _token_valido(self, token: str, proposito: str):
        ahora = datetime.now()
        registro = self.db.query(TokenSeguridadUsuario).filter(
            TokenSeguridadUsuario.token_hash == self._hash_token(token),
            TokenSeguridadUsuario.proposito == proposito,
            TokenSeguridadUsuario.usado_en.is_(None),
            TokenSeguridadUsuario.vence_en > ahora,
        ).first()
        if not registro:
            raise ValueError("El enlace no es válido o ya venció.")
        return registro

    def autenticar(self, token: str | None):
        if not token: return None
        ahora = datetime.now()
        sesion = self.db.query(SesionUsuario).filter(SesionUsuario.token_hash == self._hash_token(token), SesionUsuario.revocada_en.is_(None), SesionUsuario.vence_en > ahora).first()
        if not sesion or not sesion.usuario.activo: return None
        if sesion.ultima_actividad < ahora - self.INACTIVIDAD_MAXIMA:
            sesion.revocada_en = ahora
            self.db.commit()
            return None
        # Evita una escritura en cada petición sin debilitar el timeout ocioso.
        if sesion.ultima_actividad < ahora - timedelta(minutes=1):
            sesion.ultima_actividad = ahora
            self.db.commit()
        return sesion.usuario

    def listar_sesiones(self, usuario_id: int, token_actual: str | None = None):
        hash_actual = self._hash_token(token_actual) if token_actual else None
        ahora = datetime.now()
        sesiones = self.db.query(SesionUsuario).filter(
            SesionUsuario.usuario_id == usuario_id,
            SesionUsuario.revocada_en.is_(None),
            SesionUsuario.vence_en > ahora,
        ).order_by(SesionUsuario.ultima_actividad.desc()).all()
        return [(sesion, sesion.token_hash == hash_actual) for sesion in sesiones]

    def revocar_sesion(self, usuario_id: int, sesion_id: int):
        sesion = self.db.query(SesionUsuario).filter(
            SesionUsuario.id == sesion_id, SesionUsuario.usuario_id == usuario_id,
        ).first()
        if sesion is None:
            return False
        sesion.revocada_en = datetime.now()
        self.db.commit()
        return True

    def cerrar_sesion(self, token: str | None):
        if not token: return
        sesion = self.db.query(SesionUsuario).filter(SesionUsuario.token_hash == self._hash_token(token)).first()
        if sesion: sesion.revocada_en = datetime.now(); self.db.commit()

    def cerrar(self):
        self.db.close()
