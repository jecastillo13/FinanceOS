import streamlit as st

from components.ui.buttons import icon_button
from components.ui.cards import card_container


def account_card(cuenta):

    editar = False
    eliminar = False

    with card_container():

        top, actions = st.columns(
            [5, 1]
        )

        with top:

            st.markdown(
                f"## {cuenta.icono} {cuenta.nombre}"
            )

            st.caption(cuenta.tipo)

        with actions:

            editar = icon_button(
                "✏️",
                key=f"edit_{cuenta.id}",
                help="Editar cuenta"
            )

            eliminar = icon_button(
                "🗑️",
                key=f"delete_{cuenta.id}",
                help="Eliminar cuenta"
            )

        st.divider()

        st.caption("Saldo disponible")

        st.markdown(
            f"# {cuenta.moneda} {cuenta.saldo:,.2f}"
        )

    return editar, eliminar