import streamlit as st


def mostrar():
    st.sidebar.markdown(
        '''<div class="brand"><div class="brand-row"><div class="brand-mark">💰</div>
        <div><div class="brand-title">FinanceOS</div><div class="brand-subtitle">Tu dinero, en armonía.</div></div></div></div>
        <div class="sidebar-section">CENTRO DE CONTROL</div>''',
        unsafe_allow_html=True,
    )
    opcion = st.sidebar.radio(
        "Navegación",
        ["🏠 Dashboard", "🏦 Cuentas", "🏷️ Categorías", "💸 Movimientos", "🔁 Gastos recurrentes", "🔄 Transferencias", "📊 Presupuestos", "🎯 Metas", "📈 Inversiones", "🌎 Monedas", "📑 Reportes", "⚙️ Configuración"],
        label_visibility="collapsed",
    )
    st.sidebar.divider()
    st.sidebar.markdown('''<div class="sidebar-insight"><div class="sidebar-insight-label">ESPACIO PERSONAL</div>
    <div class="sidebar-insight-text">Tus finanzas, siempre claras ✦</div></div>
    <div class="sidebar-footer">FinanceOS · v0.6</div>''', unsafe_allow_html=True)
    return opcion
