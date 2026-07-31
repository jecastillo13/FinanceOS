import plotly.express as px
import streamlit as st

from components.cards import metric_card
from core.services import DashboardService


def mostrar():
    service = DashboardService()
    try:
        resumen = service.resumen()
        mes = service.resumen_mes()
        gastos_categoria = service.gastos_por_categoria()
        flujo = service.flujo_seis_meses()
        cuentas = service.cuentas_por_saldo()
        alertas = service.alertas_presupuesto()

        st.title("📊 Centro Financiero")
        st.caption("Una vista clara de tu patrimonio, flujo de caja y decisiones pendientes.")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            metric_card("Patrimonio", f"${resumen['patrimonio']:,.2f}", "💰")
        with col2:
            metric_card("Balance del mes", f"${mes['balance']:,.2f}", "⚖️")
        with col3:
            metric_card("Ingresos del mes", f"${mes['ingresos']:,.2f}", "⬆️")
        with col4:
            metric_card("Gastos del mes", f"${mes['gastos']:,.2f}", "⬇️")

        st.divider()
        izquierda, derecha = st.columns(2)
        with izquierda:
            st.subheader("Flujo de caja · últimos 6 meses")
            figura = px.bar(flujo, x="mes", y=["ingresos", "gastos"], barmode="group", labels={"value": "Valor", "variable": "Tipo", "mes": "Mes"}, color_discrete_map={"ingresos": "#16A34A", "gastos": "#DC2626"})
            st.plotly_chart(figura, use_container_width=True)
        with derecha:
            st.subheader("Gastos por categoría · mes actual")
            if gastos_categoria:
                figura = px.pie(gastos_categoria, names="categoría", values="valor", hole=0.45)
                st.plotly_chart(figura, use_container_width=True)
            else:
                st.info("Registra gastos para ver su distribución.")

        izquierda, derecha = st.columns(2)
        with izquierda:
            st.subheader("Cuentas")
            if cuentas:
                st.dataframe(cuentas, use_container_width=True, hide_index=True)
            else:
                st.info("Aún no hay cuentas registradas.")
        with derecha:
            st.subheader("Alertas de presupuesto")
            if not alertas:
                st.success("No hay presupuestos cerca de su límite.")
            for alerta in alertas:
                icono = "🔴" if alerta["porcentaje"] >= 100 else "🟡"
                st.warning(f"{icono} **{alerta['categoría']}**: {alerta['porcentaje']:.0f}% usado (${alerta['gastado']:,.0f} de ${alerta['límite']:,.0f}).")
    finally:
        service.cerrar()
