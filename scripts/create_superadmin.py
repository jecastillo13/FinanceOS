"""Crea un superadministrador sin exponer privilegios en la API pública."""

import argparse
import getpass
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from core.database import create_database
from core.models import Usuario
from core.services.auth_service import AuthService


def main():
    parser = argparse.ArgumentParser(description="Crear un superadministrador de FinanceOS")
    parser.add_argument("--nombre", required=True)
    parser.add_argument("--correo", required=True)
    args = parser.parse_args()
    password = getpass.getpass("Contraseña (mínimo 12 caracteres): ")
    confirmacion = getpass.getpass("Confirma la contraseña: ")
    if password != confirmacion:
        raise SystemExit("Las contraseñas no coinciden.")
    if len(password) < 12:
        raise SystemExit("La contraseña debe tener al menos 12 caracteres.")
    create_database()
    service = AuthService()
    try:
        if service.db.query(Usuario.id).filter(Usuario.rol == "superadmin").first():
            raise SystemExit("FinanceOS ya tiene un superadministrador.")
        usuario = service.crear_superadmin(args.nombre, args.correo, password)
        print(f"Superadministrador creado: {usuario.correo}")
    except ValueError as error:
        raise SystemExit(str(error)) from error
    finally:
        service.cerrar()


if __name__ == "__main__":
    main()
