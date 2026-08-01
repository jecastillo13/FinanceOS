from datetime import date

import streamlit as st

from core.services import AccountService, CategoryService, RecurringExpenseService
from components.ui.page import page_header


FRECUENCIAS = ["Semanal", "Quincenal", "Mensual", "Anual"]


def mostrar():
    page_header("🔁", "Gastos recurrentes", "Programa pagos y regístralos en Movimientos cuando los realices.", "PLANIFICACIÓN")

    service = RecurringExpenseService()
    account_service = AccountService()
    category_service = CategoryService()

    try:
        cuentas = account_service.obtener_cuentas()
        categorias = [c for c in category_service.obtener_categorias() if c.tipo == "Gasto"]
        if not categorias:
            st.warning("Crea primero una categoría de tipo Gasto para usar esta sección.")
            return

        categorias_por_id = {categoria.id: categoria for categoria in categorias}
        categoria_ids = list(categorias_por_id)
        with st.expander("➕ Nuevo gasto recurrente", expanded=True):
            with st.form("nuevo_gasto_recurrente", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    nombre = st.text_input("Nombre", placeholder="Ej: Arriendo")
                    valor = st.number_input("Valor", min_value=0.01, value=1.0, step=1000.0, format="%.2f")
                    categoria_id = st.selectbox("Categoría de gasto", categoria_ids, format_func=lambda item: categorias_por_id[item].nombre)
                with col2:
                    frecuencia = st.selectbox("Frecuencia", FRECUENCIAS, index=2)
                    proxima_fecha = st.date_input("Próxima fecha de pago", value=date.today())
                if st.form_submit_button("Guardar gasto recurrente", use_container_width=True):
                    if not nombre.strip():
                        st.error("Escribe un nombre para el gasto.")
                    else:
                        service.crear_gasto(nombre, valor, frecuencia, proxima_fecha, categoria_id)
                        st.success("Gasto recurrente creado.")
                        st.rerun()

        gastos = service.obtener_gastos(incluir_inactivos=True)
        st.divider()
        st.subheader("Mis gastos recurrentes")
        if not gastos:
            st.info("Todavía no has programado gastos recurrentes.")
            return

        cuentas_por_id = {cuenta.id: cuenta for cuenta in cuentas}
        cuenta_ids = list(cuentas_por_id)
        hoy = date.today()
        for gasto in gastos:
            estado = "Pendiente" if gasto.activo and gasto.proxima_fecha_pago <= hoy else "Programado"
            if not gasto.activo:
                estado = "Inactivo"
            with st.expander(f"{gasto.nombre} · ${gasto.valor:,.2f} · {estado}", expanded=estado == "Pendiente"):
                st.write(f"**Categoría:** {gasto.categoria.nombre} · **Frecuencia:** {gasto.frecuencia} · **Próximo pago:** {gasto.proxima_fecha_pago.strftime('%d/%m/%Y')}")
                if gasto.ultima_fecha_pago:
                    st.caption(f"Último pago registrado: {gasto.ultima_fecha_pago.strftime('%d/%m/%Y')}")

                if estado == "Pendiente":
                    if not cuenta_ids:
                        st.warning("Crea una cuenta antes de registrar el pago.")
                    else:
                        with st.form(f"pagar_gasto_{gasto.id}"):
                            cuenta_id = st.selectbox("¿Desde qué cuenta pagaste?", cuenta_ids, format_func=lambda item: f"{cuentas_por_id[item].nombre} ({cuentas_por_id[item].moneda})", key=f"cuenta_pago_{gasto.id}")
                            fecha_pago = st.date_input("Fecha de pago", value=hoy, key=f"fecha_pago_{gasto.id}")
                            if st.form_submit_button("Marcar como pagado y crear movimiento"):
                                try:
                                    service.pagar(gasto.id, cuenta_id, fecha_pago)
                                    st.success("Pago registrado en Movimientos y saldo actualizado.")
                                    st.rerun()
                                except ValueError as error:
                                    st.error(str(error))

                with st.form(f"editar_gasto_{gasto.id}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        nombre_editado = st.text_input("Nombre", value=gasto.nombre, key=f"nombre_{gasto.id}")
                        valor_editado = st.number_input("Valor", min_value=0.01, value=gasto.valor, step=1000.0, format="%.2f", key=f"valor_{gasto.id}")
                        categoria_editada = st.selectbox("Categoría", categoria_ids, index=categoria_ids.index(gasto.categoria_id), format_func=lambda item: categorias_por_id[item].nombre, key=f"categoria_{gasto.id}")
                    with col2:
                        frecuencia_editada = st.selectbox("Frecuencia", FRECUENCIAS, index=FRECUENCIAS.index(gasto.frecuencia), key=f"frecuencia_{gasto.id}")
                        proxima_fecha_editada = st.date_input("Próxima fecha", value=gasto.proxima_fecha_pago, key=f"proxima_{gasto.id}")
                        activo_editado = st.checkbox("Activo", value=bool(gasto.activo), key=f"activo_{gasto.id}")
                    if st.form_submit_button("Guardar cambios"):
                        if not nombre_editado.strip():
                            st.error("Escribe un nombre para el gasto.")
                        else:
                            service.actualizar_gasto(gasto.id, nombre_editado, valor_editado, frecuencia_editada, proxima_fecha_editada, categoria_editada, activo_editado)
                            st.success("Gasto recurrente actualizado.")
                            st.rerun()

                if st.button("Eliminar gasto recurrente", key=f"eliminar_gasto_{gasto.id}"):
                    service.eliminar_gasto(gasto.id)
                    st.success("Gasto recurrente eliminado. Los movimientos ya pagados se conservan.")
                    st.rerun()
    finally:
        service.cerrar()
        account_service.cerrar()
        category_service.cerrar()
