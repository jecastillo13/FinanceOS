from html import escape

import streamlit as st


def account_card(cuenta):
    nombre = escape(cuenta.nombre)
    tipo = escape(cuenta.tipo)
    moneda = escape(cuenta.moneda)
    color = escape(cuenta.color or "#818CF8")
    icono = escape(cuenta.icono or "🏦")

    st.markdown(
        f'''<div class="account-card">
            <div class="account-card-top">
                <div class="account-card-icon" style="background:{color}">{icono}</div>
                <div><div class="account-card-name">{nombre}</div><div class="account-card-type">{tipo}</div></div>
                <div class="account-card-badge">{moneda}</div>
            </div>
            <div class="account-card-divider"></div>
            <div class="account-card-label">SALDO DISPONIBLE</div>
            <div class="account-card-balance">{moneda} {cuenta.saldo:,.2f}</div>
        </div>''',
        unsafe_allow_html=True,
    )

    editar_col, eliminar_col = st.columns(2)
    with editar_col:
        editar = st.button("Editar", key=f"edit_{cuenta.id}", use_container_width=True)
    with eliminar_col:
        eliminar = st.button("Eliminar", key=f"delete_{cuenta.id}", use_container_width=True)
    return editar, eliminar
