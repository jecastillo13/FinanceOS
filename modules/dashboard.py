import plotly.express as px
import streamlit as st

from components.cards import metric_card
from core.services import DashboardService


def mostrar():
    service = DashboardService()
    try:
        resumen = service.resumen()
        mes = service.resumen_mes()
        gastos_categoria, pendientes_gastos = service.gastos_por_categoria()
        flujo = service.flujo_seis_meses()
        cuentas, pendientes_cuentas = service.cuentas_por_saldo()
        alertas, pendientes_alertas = service.alertas_presupuesto()

        st.title("📊 Centro Financiero")
        st.caption("Una vista clara de tu patrimonio, flujo de caja y decisiones pendientes.")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            metric_card("Patrimonio", f"COP ${resumen['patrimonio']:,.2f}", "💰", "Consolidado en pesos colombianos")
        with col2:
            metric_card("Balance del mes", f"COP ${mes['balance']:,.2f}", "⚖️")
        with col3:
            metric_card("Ingresos del mes", f"COP ${mes['ingresos']:,.2f}", "⬆️")
        with col4:
            metric_card("Gastos del mes", f"COP ${mes['gastos']:,.2f}", "⬇️")

        pendientes = {cuenta.id: cuenta for cuenta in resumen["pendientes"] + pendientes_gastos + pendientes_cuentas + pendientes_alertas}
        if pendientes:
            nombres = ", ".join(f"{cuenta.nombre} ({cuenta.moneda})" for cuenta in pendientes.values())
            st.warning(f"Algunos valores no se consolidaron en COP porque falta una tasa para: {nombres}. Actualízala en Monedas.")

        st.divider()
        izquierda, derecha = st.columns(2)
        with izquierda:
            st.subheader("Flujo de caja · últimos 6 meses")
            if any(fila["ingresos"] or fila["gastos"] for fila in flujo):
                figura = px.bar(flujo, x="mes", y=["ingresos", "gastos"], barmode="group", labels={"value": "COP", "variable": "Tipo", "mes": "Mes"}, color_discrete_map={"ingresos": "#16A34A", "gastos": "#DC2626"})
                figura.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(20,27,46,.65)", legend_title_text="", margin=dict(l=10, r=10, t=20, b=10))
                st.plotly_chart(figura, use_container_width=True)
            else:
                st.info("Registra tu primer movimiento para ver el flujo de caja.")
        with derecha:
            st.subheader("Gastos por categoría · mes actual")
            if gastos_categoria:
                figura = px.pie(gastos_categoria, names="categoría", values="valor", hole=0.45)
                figura.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", legend_title_text="", margin=dict(l=10, r=10, t=20, b=10))
                st.plotly_chart(figura, use_container_width=True)
            else:
                st.info("Registra gastos para ver su distribución.")

        izquierda, derecha = st.columns(2)
        with izquierda:
            st.subheader("Distribución de patrimonio")
            if cuentas:
                figura = px.pie(cuentas, names="cuenta", values="saldo_cop", hole=0.58, color_discrete_sequence=["#818CF8", "#34D399", "#38BDF8", "#FBBF24", "#FB7185"])
                figura.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", legend_title_text="", margin=dict(l=10, r=10, t=20, b=10))
                st.plotly_chart(figura, use_container_width=True)
                st.caption("Saldos convertidos y consolidados en COP.")
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
