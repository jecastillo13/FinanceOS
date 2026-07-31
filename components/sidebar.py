import streamlit as st


def mostrar():

    st.sidebar.image(
        "https://img.icons8.com/fluency/96/money-bag.png",
        width=70
    )

    st.sidebar.title("FinanceOS")

    st.sidebar.markdown("## 💰 Finanzas")

    opcion = st.sidebar.radio(
        "Navegación",
        [
            "🏠 Dashboard",
            "🏦 Cuentas",
            "🏷 Categorías",
            "💸 Movimientos",
            "🎯 Metas",
            "📈 Inversiones",
             "🌎 Monedas",
            "📊 Reportes",
            "⚙ Configuración"
        ]
    )

    st.sidebar.divider()

    st.sidebar.caption("FinanceOS v0.6")

    return opcion