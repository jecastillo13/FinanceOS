import streamlit as st

from core.services.account_service import AccountService


@st.dialog("✏️ Editar cuenta")
def edit_account_dialog(cuenta):

    service = AccountService()

    tipos = [
        "Ahorros",
        "Corriente",
        "Crédito",
        "Efectivo",
        "Inversión"
    ]

    monedas = [
        "COP",
        "USD",
        "EUR"
    ]

    nombre = st.text_input(
        "Nombre",
        value=cuenta.nombre,
        key=f"edit_nombre_{cuenta.id}"
    )

    tipo = st.selectbox(
        "Tipo",
        tipos,
        index=tipos.index(cuenta.tipo),
        key=f"edit_tipo_{cuenta.id}"
    )

    saldo = st.number_input(
        "Saldo",
        value=float(cuenta.saldo),
        step=1000.0,
        key=f"edit_saldo_{cuenta.id}"
    )

    moneda = st.selectbox(
        "Moneda",
        monedas,
        index=monedas.index(cuenta.moneda),
        key=f"edit_moneda_{cuenta.id}"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "Cancelar",
            key=f"cancelar_{cuenta.id}",
            use_container_width=True
        ):

            if "editar_cuenta" in st.session_state:
                del st.session_state["editar_cuenta"]

            service.cerrar()

            st.rerun()

    with col2:

        if st.button(
            "Guardar cambios",
            key=f"guardar_{cuenta.id}",
            type="primary",
            use_container_width=True
        ):

            service.actualizar_cuenta(
                cuenta.id,
                nombre,
                tipo,
                saldo,
                moneda,
                cuenta.color,
                cuenta.icono
            )

            service.cerrar()

            if "editar_cuenta" in st.session_state:
                del st.session_state["editar_cuenta"]

            st.success("✅ Cuenta actualizada correctamente.")

            st.rerun()