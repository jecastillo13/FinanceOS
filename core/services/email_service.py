"""Entrega de correos transaccionales sin acoplar la autenticación al proveedor."""

import os
import smtplib
from email.message import EmailMessage
from pathlib import Path


class EmailService:
    def __init__(self):
        self.host = os.getenv("FINANCEOS_SMTP_HOST", "").strip()
        self.port = int(os.getenv("FINANCEOS_SMTP_PORT", "587"))
        self.usuario = os.getenv("FINANCEOS_SMTP_USER", "").strip()
        self.password = os.getenv("FINANCEOS_SMTP_PASSWORD", "")
        self.remitente = os.getenv("FINANCEOS_EMAIL_FROM", self.usuario or "no-reply@financeos.local")
        self.base_url = os.getenv("FINANCEOS_PUBLIC_URL", "http://localhost:8000").rstrip("/")

    def _enviar(self, destino: str, asunto: str, texto: str):
        if not self.host:
            # Bandeja local deliberadamente ignorada por Git. Permite probar el
            # flujo sin fingir que hubo una entrega real.
            ruta = Path(__file__).resolve().parents[2] / "database" / "correo-desarrollo.txt"
            ruta.parent.mkdir(parents=True, exist_ok=True)
            with ruta.open("a", encoding="utf-8") as archivo:
                archivo.write(f"\nPARA: {destino}\nASUNTO: {asunto}\n{texto}\n")
            return "desarrollo"
        mensaje = EmailMessage()
        mensaje["From"], mensaje["To"], mensaje["Subject"] = self.remitente, destino, asunto
        mensaje.set_content(texto)
        with smtplib.SMTP(self.host, self.port, timeout=15) as smtp:
            smtp.starttls()
            if self.usuario:
                smtp.login(self.usuario, self.password)
            smtp.send_message(mensaje)
        return "enviado"

    def enviar_verificacion(self, correo: str, token: str):
        enlace = f"{self.base_url}/verificar-correo?token={token}"
        return self._enviar(correo, "Verifica tu cuenta de FinanceOS", f"Confirma tu correo abriendo este enlace (vence en 24 horas):\n\n{enlace}")

    def enviar_recuperacion(self, correo: str, token: str):
        enlace = f"{self.base_url}/recuperar-clave?token={token}"
        return self._enviar(correo, "Recupera tu acceso a FinanceOS", f"Crea una contraseña nueva desde este enlace de un solo uso (vence en 30 minutos):\n\n{enlace}\n\nSi no lo solicitaste, ignora este mensaje.")
