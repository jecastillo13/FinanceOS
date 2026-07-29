"""
modules/movimientos.py

IMPORTANTE:
El archivo que se estaba construyendo en el chat quedó incompleto por el
límite de longitud de los mensajes. El error "NameError: cuentas is not defined"
se debe a que parte del formulario quedó fuera de la función mostrar().

Para evitar entregarte un archivo roto, este archivo contiene la estructura
correcta y sirve como base para reemplazar el módulo dañado.

Necesita completarse con el resto del historial y acciones CRUD si deseas
todas las funcionalidades.
"""

import streamlit as st

from core.services import MovementService, AccountService
from core.database import get_session
from core.models import Categoria


def mostrar():
    st.title("💸 Movimientos")

    movement_service = MovementService()
    account_service = AccountService()
    db = get_session()

    cuentas = account_service.obtener_cuentas()

    categorias = (
        db.query(Categoria)
        .order_by(Categoria.tipo, Categoria.nombre)
        .all()
    )

    if not cuentas:
        st.warning("Primero crea una cuenta.")
        movement_service.cerrar()
        account_service.cerrar()
        db.close()
        return

    if not categorias:
        st.warning("No existen categorías.")
        movement_service.cerrar()
        account_service.cerrar()
        db.close()
        return

    st.info(
        "La versión anterior quedó dañada por un problema de indentación. "
        "Este archivo restaura la estructura correcta del módulo."
    )

    movement_service.cerrar()
    account_service.cerrar()
    db.close()
