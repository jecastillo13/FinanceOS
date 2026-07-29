import streamlit as st

from core.services.account_service import AccountService
from components.account_card import account_card
from components.dialogs.edit_account_dialog import edit_account_dialog


def mostrar():

    st.title("🏦 Gestión de Cuentas")
    st.caption("Administra todas tus cuentas financieras.")

    service = AccountService()

    # =====================================================
    # NUEVA CUENTA
    # =====================================================

    with st.expander("➕ Nueva cuenta", expanded=True):

        col1, col2 = st.columns(2)

        with col1:

            nombre = st.text_input(
                "Nombre de la cuenta",
                placeholder="Ej: Bancolombia"
            )

            tipo = st.selectbox(
                "Tipo",
                [
                    "Ahorros",
                    "Corriente",
                    "Crédito",
                    "Efectivo",
                    "Inversión"
                ]
            )

        with col2:

            saldo = st.number_input(
                "Saldo inicial",
                value=0.0,
                step=1000.0,
                format="%.2f"
            )

            moneda = st.selectbox(
                "Moneda",
                [
                    "COP",
                    "USD",
                    "EUR"
                ]
            )

        if st.button(
            "💾 Guardar cuenta",
            use_container_width=True
        ):

            if nombre.strip() == "":

                st.error("Debes escribir un nombre.")

            else:

                iconos = {
                    "Ahorros": "🏦",
                    "Corriente": "💳",
                    "Crédito": "💳",
                    "Efectivo": "💵",
                    "Inversión": "📈"
                }

                colores = {
                    "Ahorros": "#22C55E",
                    "Corriente": "#3B82F6",
                    "Crédito": "#EF4444",
                    "Efectivo": "#F59E0B",
                    "Inversión": "#8B5CF6"
                }

                service.crear_cuenta(
                    nombre=nombre,
                    tipo=tipo,
                    saldo=saldo,
                    moneda=moneda,
                    icono=iconos[tipo],
                    color=colores[tipo]
                )

                service.cerrar()

                st.success("✅ Cuenta creada correctamente.")

                st.rerun()

    st.divider()

    # =====================================================
    # LISTA DE CUENTAS
    # =====================================================

    cuentas = service.obtener_cuentas()

    if not cuentas:

        st.info("Todavía no existen cuentas.")

    else:

        st.subheader("🏦 Mis cuentas")

        col1, col2 = st.columns(2)

        for i, cuenta in enumerate(cuentas):

            columna = col1 if i % 2 == 0 else col2

            with columna:

                editar, eliminar = account_card(cuenta)

                if editar:

                    st.session_state["editar_cuenta"] = cuenta.id
                    st.rerun()

                if eliminar:

                    st.session_state["eliminar_cuenta"] = cuenta.id
                    st.rerun()

    # =====================================================
    # EDITAR
    # =====================================================

    if "editar_cuenta" in st.session_state:

        cuenta = service.obtener_cuenta(
            st.session_state["editar_cuenta"]
        )

        if cuenta:

            edit_account_dialog(cuenta)

    # =====================================================
    # ELIMINAR
    # =====================================================

    if "eliminar_cuenta" in st.session_state:

        cuenta = service.obtener_cuenta(
            st.session_state["eliminar_cuenta"]
        )

        if cuenta:

            st.warning(
                f"¿Eliminar la cuenta **{cuenta.nombre}**?"
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "🗑 Eliminar",
                    key=f"delete_confirm_{cuenta.id}",
                    use_container_width=True
                ):

                    service.eliminar_cuenta(cuenta.id)

                    del st.session_state["eliminar_cuenta"]

                    service.cerrar()

                    st.success("Cuenta eliminada correctamente.")

                    st.rerun()

            with col2:

                if st.button(
                    "Cancelar",
                    key=f"cancel_delete_{cuenta.id}",
                    use_container_width=True
                ):

                    del st.session_state["eliminar_cuenta"]

                    st.rerun()

    service.cerrar()