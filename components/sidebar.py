import streamlit as st


def mostrar():

    st.sidebar.image(
        "https://img.icons8.com/fluency/96/money-bag.png",
        width=70
    )

    st.sidebar.title("FinanceOS")

    opcion = st.sidebar.radio(
        "Navegación",
        [
            "🏠 Dashboard",
            "🏦 Cuentas",
            "💸 Movimientos",
            "🎯 Metas",
            "📈 Inversiones",
            "📊 Reportes",
            "⚙ Configuración"
        ]
    )

    st.sidebar.divider()

    st.sidebar.caption("FinanceOS v0.5")

    return opcion