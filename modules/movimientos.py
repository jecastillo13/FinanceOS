from datetime import date

import streamlit as st

from core.services import AccountService, AttachmentService, CategoryService, MovementService
from components.ui.page import page_header
from components.dialogs.delete_confirmation import confirm_delete


def _etiqueta_categoria(categoria):
    return f"{categoria.tipo}: {categoria.nombre}"


@st.dialog("✏️ Editar movimiento")
def editar_movimiento_dialog(service, attachment_service, movimiento, cuentas_por_id, categorias_por_id):
    cuenta_ids = list(cuentas_por_id)
    categoria_ids = list(categorias_por_id)
    with st.form(f"editar_movimiento_{movimiento.id}"):
        edit_col1, edit_col2 = st.columns(2)
        with edit_col1:
            fecha_editada = st.date_input("Fecha", value=movimiento.fecha, key=f"fecha_{movimiento.id}")
            cuenta_editada = st.selectbox("Cuenta", cuenta_ids, index=cuenta_ids.index(movimiento.cuenta_id), format_func=lambda item: f"{cuentas_por_id[item].nombre} ({cuentas_por_id[item].moneda})", key=f"cuenta_{movimiento.id}")
            categoria_editada = st.selectbox("Categoría", categoria_ids, index=categoria_ids.index(movimiento.categoria_id), format_func=lambda item: _etiqueta_categoria(categorias_por_id[item]), key=f"categoria_{movimiento.id}")
        with edit_col2:
            descripcion_editada = st.text_input("Descripción", value=movimiento.descripcion or "", key=f"descripcion_{movimiento.id}")
            valor_editado = st.number_input("Valor", min_value=0.01, value=abs(movimiento.valor), step=1000.0, format="%.2f", key=f"valor_{movimiento.id}")
            observaciones_editadas = st.text_area("Observaciones", value=movimiento.observaciones or "", key=f"observaciones_{movimiento.id}")
            comprobante = st.file_uploader("Añadir comprobante", type=["jpg", "jpeg", "png", "webp", "pdf"], key=f"comprobante_{movimiento.id}")
        if st.form_submit_button("Guardar cambios", use_container_width=True):
            service.actualizar_movimiento(movimiento.id, fecha_editada, descripcion_editada.strip(), valor_editado, cuenta_editada, categoria_editada, observaciones_editadas.strip())
            if comprobante:
                attachment_service.guardar(movimiento.id, comprobante.name, comprobante.getvalue(), comprobante.type)
            st.success("Movimiento actualizado.")
            st.rerun()

    adjuntos = attachment_service.obtener_por_movimiento(movimiento.id)
    if adjuntos:
        st.caption(f"Comprobantes adjuntos: {len(adjuntos)}")
        for adjunto in adjuntos:
            contenido = attachment_service.leer(adjunto)
            if contenido:
                st.download_button(f"Descargar {adjunto.nombre}", data=contenido, file_name=adjunto.nombre, mime=adjunto.tipo_mime, key=f"descargar_adjunto_{adjunto.id}")


def mostrar():
    page_header("💸", "Movimientos", "Registra ingresos y gastos; la categoría define el signo automáticamente.", "ACTIVIDAD")

    movement_service = MovementService()
    attachment_service = AttachmentService()
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
                    comprobante = st.file_uploader("Comprobante (opcional)", type=["jpg", "jpeg", "png", "webp", "pdf"])

                guardar = st.form_submit_button("Guardar movimiento", use_container_width=True)

                if guardar:
                    movimiento = movement_service.registrar_movimiento(
                        fecha, descripcion.strip(), valor, cuenta_id, categoria_id, observaciones.strip()
                    )
                    if comprobante:
                        attachment_service.guardar(movimiento.id, comprobante.name, comprobante.getvalue(), comprobante.type)
                    st.success("Movimiento registrado correctamente.")
                    st.rerun()

        st.divider()
        st.subheader("Historial")

        filtro_columna, limite_columna = st.columns([3, 1])
        with filtro_columna:
            busqueda = st.text_input("Buscar en historial", placeholder="Descripción, categoría o cuenta")
        with limite_columna:
            limite_historial = st.selectbox("Por página", [25, 50, 100], index=1)

        total_movimientos = movement_service.contar_movimientos(busqueda)
        total_paginas = max(1, (total_movimientos + limite_historial - 1) // limite_historial)
        pagina_actual = st.number_input(
            "Página",
            min_value=1,
            max_value=total_paginas,
            value=1,
            step=1,
            key=f"pagina_movimientos_{busqueda.strip().lower() or 'todos'}_{limite_historial}",
        )
        desplazamiento = (pagina_actual - 1) * limite_historial
        movimientos = movement_service.obtener_movimientos(limite_historial, desplazamiento, busqueda)
        st.caption(f"Mostrando {len(movimientos)} de {total_movimientos} movimiento(s).")

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

                if st.button("Editar movimiento", key=f"editar_movimiento_{movimiento.id}"):
                    editar_movimiento_dialog(movement_service, attachment_service, movimiento, cuentas_por_id, categorias_por_id)

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
        attachment_service.cerrar()
        account_service.cerrar()
        category_service.cerrar()
