from datetime import date

import streamlit as st

from core.services import AccountService, CategoryService, MovementService
from components.ui.page import page_header
from components.dialogs.delete_confirmation import confirm_delete


def _etiqueta_categoria(categoria):
    return f"{categoria.tipo}: {categoria.nombre}"


def mostrar():
    page_header("💸", "Movimientos", "Registra ingresos y gastos; la categoría define el signo automáticamente.", "ACTIVIDAD")

    movement_service = MovementService()
    account_service = AccountService()
    category_service = CategoryService()

    try:
        cuentas = account_service.obtener_cuentas()
        categorias = [categoria for categoria in category_service.obtener_categorias() if categoria.activa and categoria.tipo in ("Ingreso", "Gasto")]

        if not cuentas:
            st.warning("Primero crea una cuenta.")
            return

        if not categorias:
            st.warning("Primero crea al menos una categoría.")
            return

        cuentas_por_id = {cuenta.id: cuenta for cuenta in cuentas}
        categorias_por_id = {categoria.id: categoria for categoria in categorias}
        cuenta_ids = list(cuentas_por_id)
        categoria_ids = list(categorias_por_id)

        with st.expander("➕ Nuevo movimiento", expanded=True):
            with st.form("form_movimiento", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    fecha = st.date_input("Fecha", value=date.today())
                    cuenta_id = st.selectbox(
                        "Cuenta",
                        cuenta_ids,
                        format_func=lambda item: f"{cuentas_por_id[item].nombre} ({cuentas_por_id[item].moneda})",
                    )
                    categoria_id = st.selectbox(
                        "Categoría",
                        categoria_ids,
                        format_func=lambda item: _etiqueta_categoria(categorias_por_id[item]),
                    )
                with col2:
                    descripcion = st.text_input("Descripción", placeholder="Ej: Nómina de julio")
                    valor = st.number_input("Valor", min_value=0.01, value=1.0, step=1000.0, format="%.2f")
                    observaciones = st.text_area("Observaciones", placeholder="Opcional")

                guardar = st.form_submit_button("Guardar movimiento", use_container_width=True)

                if guardar:
                    movement_service.registrar_movimiento(
                        fecha, descripcion.strip(), valor, cuenta_id, categoria_id, observaciones.strip()
                    )
                    st.success("Movimiento registrado correctamente.")
                    st.rerun()

        movimientos = movement_service.obtener_movimientos()
        st.divider()
        st.subheader("Historial")

        if not movimientos:
            st.info("Todavía no hay movimientos registrados.")
            return

        for movimiento in movimientos:
            categoria = movimiento.categoria
            cuenta = movimiento.cuenta
            signo = "+" if movimiento.valor >= 0 else "-"
            color = "#16A34A" if movimiento.valor >= 0 else "#DC2626"

            with st.expander(
                f"{movimiento.fecha.strftime('%d/%m/%Y')} · {movimiento.descripcion or categoria.nombre} · {signo}${abs(movimiento.valor):,.2f}",
                expanded=False,
            ):
                col1, col2, col3 = st.columns([3, 2, 2])
                col1.write(f"**Cuenta:** {cuenta.nombre} ({cuenta.moneda})")
                col2.markdown(f"**Categoría:** :{color}[{categoria.nombre}]")
                col3.markdown(f"**Valor:** :{color}[{signo}${abs(movimiento.valor):,.2f}]")
                if movimiento.observaciones:
                    st.caption(movimiento.observaciones)

                with st.form(f"editar_movimiento_{movimiento.id}"):
                    edit_col1, edit_col2 = st.columns(2)
                    with edit_col1:
                        fecha_editada = st.date_input("Fecha", value=movimiento.fecha, key=f"fecha_{movimiento.id}")
                        cuenta_editada = st.selectbox(
                            "Cuenta", cuenta_ids, index=cuenta_ids.index(movimiento.cuenta_id),
                            format_func=lambda item: f"{cuentas_por_id[item].nombre} ({cuentas_por_id[item].moneda})",
                            key=f"cuenta_{movimiento.id}",
                        )
                        categoria_editada = st.selectbox(
                            "Categoría", categoria_ids, index=categoria_ids.index(movimiento.categoria_id),
                            format_func=lambda item: _etiqueta_categoria(categorias_por_id[item]),
                            key=f"categoria_{movimiento.id}",
                        )
                    with edit_col2:
                        descripcion_editada = st.text_input("Descripción", value=movimiento.descripcion or "", key=f"descripcion_{movimiento.id}")
                        valor_editado = st.number_input("Valor", min_value=0.01, value=abs(movimiento.valor), step=1000.0, format="%.2f", key=f"valor_{movimiento.id}")
                        observaciones_editadas = st.text_area("Observaciones", value=movimiento.observaciones or "", key=f"observaciones_{movimiento.id}")

                    guardar_cambios = st.form_submit_button("Guardar cambios")
                    if guardar_cambios:
                        movement_service.actualizar_movimiento(
                            movimiento.id, fecha_editada, descripcion_editada.strip(), valor_editado,
                            cuenta_editada, categoria_editada, observaciones_editadas.strip(),
                        )
                        st.success("Movimiento actualizado.")
                        st.rerun()

                if st.button("Eliminar movimiento", key=f"eliminar_movimiento_{movimiento.id}"):
                    confirm_delete(
                        "¿Eliminar movimiento?",
                        movimiento.descripcion or "Este movimiento no tiene descripción.",
                        "El saldo de la cuenta se restaurará automáticamente.",
                        lambda: movement_service.eliminar_movimiento(movimiento.id) or True,
                        "Movimiento eliminado y saldo restaurado.",
                    )
    finally:
        movement_service.cerrar()
        account_service.cerrar()
        category_service.cerrar()
