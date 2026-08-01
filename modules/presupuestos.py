from datetime import date

import streamlit as st

from core.services import BudgetService, CategoryService


MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def mostrar():
    st.title("📊 Presupuestos mensuales")
    st.caption("Define límites en COP por categoría y controla el gasto de cada mes.")
    budget_service = BudgetService()
    category_service = CategoryService()

    try:
        hoy = date.today()
        col1, col2 = st.columns(2)
        with col1:
            anio = st.number_input("Año", min_value=2020, max_value=2100, value=hoy.year, step=1)
        with col2:
            mes = st.selectbox("Mes", range(1, 13), index=hoy.month - 1, format_func=lambda item: MESES[item - 1])

        categorias = [c for c in category_service.obtener_categorias() if c.tipo == "Gasto" and c.activa]
        if not categorias:
            st.warning("Necesitas categorías de gasto activas para crear presupuestos.")
            return

        categorias_por_id = {categoria.id: categoria for categoria in categorias}
        categoria_ids = list(categorias_por_id)
        with st.expander("➕ Crear o actualizar presupuesto", expanded=True):
            with st.form("guardar_presupuesto", clear_on_submit=True):
                categoria_id = st.selectbox("Categoría", categoria_ids, format_func=lambda item: f"{categorias_por_id[item].icono or '🏷️'} {categorias_por_id[item].nombre}")
                valor = st.number_input("Presupuesto mensual (COP)", min_value=0.01, value=1.0, step=10000.0, format="%.2f")
                if st.form_submit_button("Guardar presupuesto", use_container_width=True):
                    budget_service.guardar_presupuesto(anio, mes, categoria_id, valor)
                    st.success("Presupuesto guardado.")
                    st.rerun()

        st.divider()
        st.subheader(f"Resumen · {MESES[mes - 1]} {anio}")
        resumen = budget_service.resumen(anio, mes)
        if not resumen:
            st.info("Aún no hay presupuestos para este período.")
            return

        total_presupuesto = sum(item["presupuesto"].valor for item in resumen)
        total_gastado = sum(item["gastado"] for item in resumen)
        st.metric("Presupuesto total", f"${total_presupuesto:,.2f}", f"Gastado: ${total_gastado:,.2f}")

        for item in resumen:
            presupuesto = item["presupuesto"]
            gastado = item["gastado"]
            porcentaje = (gastado / presupuesto.valor * 100) if presupuesto.valor else 0
            progreso = min(porcentaje / 100, 1.0)
            if porcentaje >= 100:
                estado = "🔴 Límite superado" if porcentaje > 100 else "🔴 Límite alcanzado"
            elif porcentaje >= 80:
                estado = "🟡 Cerca del límite"
            else:
                estado = "🟢 En control"

            with st.expander(f"{presupuesto.categoria.icono or '🏷️'} {presupuesto.categoria.nombre} · {porcentaje:.0f}% · {estado}", expanded=porcentaje >= 80):
                st.write(f"Presupuesto: **${presupuesto.valor:,.2f}** · Gastado: **${gastado:,.2f}** · Disponible: **${presupuesto.valor - gastado:,.2f}**")
                st.progress(progreso)
                if st.button("Eliminar presupuesto", key=f"eliminar_presupuesto_{presupuesto.id}"):
                    budget_service.eliminar_presupuesto(presupuesto.id)
                    st.success("Presupuesto eliminado.")
                    st.rerun()
    finally:
        budget_service.cerrar()
        category_service.cerrar()
