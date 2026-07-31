import streamlit as st


def mostrar():
    st.sidebar.markdown(
        '''<div class="brand"><div class="brand-mark">💰</div>
        <div class="brand-title">FinanceOS</div><div class="brand-subtitle">Finanzas personales, claras.</div></div>''',
        unsafe_allow_html=True,
    )
    opcion = st.sidebar.radio(
        "Navegación",
        ["🏠 Dashboard", "🏦 Cuentas", "🏷️ Categorías", "💸 Movimientos", "🔁 Gastos recurrentes", "🔄 Transferencias", "📊 Presupuestos", "🎯 Metas", "📈 Inversiones", "🌎 Monedas", "📑 Reportes", "⚙️ Configuración"],
        label_visibility="collapsed",
    )
    st.sidebar.divider()
    st.sidebar.caption("FinanceOS · v0.6")
    return opcion
