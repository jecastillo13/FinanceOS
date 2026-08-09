import streamlit as st

from components.cards import metric_card
from components.charts import dona_chart, flujo_caja_chart
from components.ui.page import page_header
from core.services import DashboardService


def _es_movil():
    agente = st.context.headers.get("User-Agent", "").lower()
    return any(dispositivo in agente for dispositivo in ("android", "iphone", "ipad", "mobile"))


def _mostrar_alertas(alertas, compacto=False):
    if not alertas:
        st.success("No hay presupuestos cerca de su límite.")
    for alerta in alertas:
        icono = "🔴" if alerta["porcentaje"] >= 100 else "🟡"
        if compacto:
            st.warning(f"{icono} **{alerta['categoría']}**: {alerta['porcentaje']:.0f}% usado.")
        else:
            st.warning(
                f"{icono} **{alerta['categoría']}**: {alerta['porcentaje']:.0f}% usado "
                f"(${alerta['gastado']:,.0f} de ${alerta['límite']:,.0f})."
            )


def mostrar():
    service = DashboardService()
    try:
        movil = _es_movil()
        resumen = service.resumen()
        cuentas, pendientes_cuentas = service.cuentas_por_saldo()
        inversiones, pendientes_inversiones = service.inversiones_por_saldo()
        alertas, pendientes_alertas = service.alertas_presupuesto()
        gastos_categoria, pendientes_gastos, flujo = [], [], []
        if not movil:
            gastos_categoria, pendientes_gastos = service.gastos_por_categoria()
            flujo = service.flujo_seis_meses()

        page_header("📊", "Centro Financiero", "Una vista clara de tu patrimonio, flujo de caja y decisiones pendientes.", "RESUMEN GENERAL")
        columnas = st.columns(2) if movil else st.columns(4)
        metricas = [
            ("Patrimonio", f"COP ${resumen['patrimonio']:,.2f}", "💰", f"Cuentas ${resumen['cuentas_cop']:,.0f} · inversiones ${resumen['inversiones_cop']:,.0f}"),
            ("Balance del mes", f"COP ${resumen['balance']:,.2f}", "⚖️", ""),
            ("Ingresos del mes", f"COP ${resumen['ingresos']:,.2f}", "⬆️", ""),
            ("Gastos del mes", f"COP ${resumen['gastos']:,.2f}", "⬇️", ""),
        ]
        for columna, metrica in zip(columnas * 2 if movil else columnas, metricas):
            with columna:
                metric_card(*metrica)

        pendientes = {
            cuenta.id: cuenta
            for cuenta in resumen["pendientes"] + pendientes_gastos + pendientes_cuentas + pendientes_alertas
        }
        if pendientes:
            nombres = ", ".join(f"{cuenta.nombre} ({cuenta.moneda})" for cuenta in pendientes.values())
            st.warning(f"Algunos valores no se consolidaron en COP porque falta una tasa para: {nombres}. Actualízala en Monedas.")
        if pendientes_inversiones:
            activos = ", ".join(f"{inversion.activo} ({inversion.moneda})" for inversion in pendientes_inversiones)
            st.warning(f"No se incluyeron estas inversiones en el patrimonio por falta de tasa: {activos}.")

        st.divider()
        if movil:
            st.caption("Vista móvil ligera: las gráficas se muestran en escritorio para cargar más rápido.")
            st.subheader("Tus cuentas")
            for cuenta in cuentas[:5]:
                st.write(f"**{cuenta['cuenta']}** · COP ${cuenta['saldo_cop']:,.2f}")
            if inversiones:
                st.subheader("Tus inversiones")
                for inversion in inversiones[:5]:
                    st.write(f"**{inversion['cuenta']}** · COP ${inversion['saldo_cop']:,.2f}")
            st.subheader("Alertas de presupuesto")
            _mostrar_alertas(alertas, compacto=True)
            return

        izquierda, derecha = st.columns(2)
        with izquierda:
            st.subheader("Flujo de caja · últimos 6 meses")
            if any(fila["ingresos"] or fila["gastos"] for fila in flujo):
                st.plotly_chart(flujo_caja_chart(flujo), use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Registra tu primer movimiento para ver el flujo de caja.")
        with derecha:
            st.subheader("Gastos por categoría · mes actual")
            if gastos_categoria:
                st.plotly_chart(dona_chart(gastos_categoria, "categoría", "valor", centro="GASTOS"), use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Registra gastos para ver su distribución.")

        izquierda, derecha = st.columns(2)
        with izquierda:
            st.subheader("Distribución de patrimonio")
            distribucion = cuentas + inversiones
            if distribucion:
                st.plotly_chart(dona_chart(distribucion, "cuenta", "saldo_cop", centro="PATRIMONIO"), use_container_width=True, config={"displayModeBar": False})
                st.caption("Cuentas e inversiones convertidas y consolidadas en COP.")
            else:
                st.info("Aún no hay cuentas ni inversiones registradas.")
        with derecha:
            st.subheader("Alertas de presupuesto")
            _mostrar_alertas(alertas)
    finally:
        service.cerrar()
