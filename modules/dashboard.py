import streamlit as st

from core.services import DashboardService
from components.cards import metric_card


def mostrar():

    service = DashboardService()

    resumen = service.resumen()

    patrimonio = resumen["patrimonio"]
    cuentas = resumen["cuentas"]
    inversiones = resumen["inversiones"]
    ingresos = resumen["ingresos"]
    gastos = resumen["gastos"]
    metas = resumen["metas"]

    st.title("📊 Dashboard")
    st.caption("Tu centro de control financiero")

    # =====================================================
    # PRIMERA FILA
    # =====================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        metric_card(
            "Patrimonio",
            f"${patrimonio:,.2f}",
            "💰"
        )

    with col2:

        metric_card(
            "Cuentas",
            cuentas,
            "🏦"
        )

    with col3:

        metric_card(
            "Inversiones",
            f"${inversiones:,.2f}",
            "📈"
        )

    st.divider()

    # =====================================================
    # SEGUNDA FILA
    # =====================================================

    col1, col2, col3 = st.columns(3)

    with col1:

        metric_card(
            "Ingresos",
            f"${ingresos:,.2f}",
            "⬆️"
        )

    with col2:

        metric_card(
            "Gastos",
            f"${gastos:,.2f}",
            "⬇️"
        )

    with col3:

        metric_card(
            "Metas",
            metas,
            "🎯"
        )

    st.divider()

    # =====================================================
    # PANEL INFERIOR
    # =====================================================

    izquierda, derecha = st.columns([2, 1])

    with izquierda:

        st.subheader("📊 Resumen")

        st.info(
            """
### Cuando registres información aparecerá automáticamente:

- 📈 Evolución del patrimonio
- 💸 Flujo de caja
- 🥧 Gastos por categoría
- 📅 Ingresos mensuales
- 📊 Balance mensual
- 📈 Evolución de inversiones
- 🎯 Progreso de metas
            """
        )

    with derecha:

        st.subheader("⚡ Estado")

        st.success("✅ Base de datos conectada")
        st.success("✅ Dashboard operativo")

        if cuentas == 0:
            st.warning("⚠️ No hay cuentas registradas")

        if metas == 0:
            st.info("🎯 No hay metas creadas")

        if patrimonio == 0:
            st.error("💰 Patrimonio actual: $0")

    service.cerrar()