from datetime import date

import streamlit as st

from components.ui.page import page_header
from components.dialogs.delete_confirmation import confirm_delete
from core.services import AccountService, CategoryService, GoalService


def _dinero(valor, moneda):
    return f"{moneda} {valor:,.2f}"


@st.dialog("⚠️ Eliminar meta")
def confirmar_eliminacion(service, meta_id, nombre, aportes, pagos):
    st.markdown(f"## ¿Eliminar **{nombre}**?")
    st.caption("Esta acción eliminará la planificación y sus registros asociados.")
    columna_aportes, columna_pagos = st.columns(2)
    columna_aportes.metric("Aportes registrados", aportes)
    columna_pagos.metric("Pagos y movimientos", pagos)
    st.warning(
        "Los pagos también eliminarán sus movimientos financieros y restaurarán los saldos de las cuentas utilizadas."
    )
    cancelar, eliminar = st.columns(2)
    with cancelar:
        if st.button("Conservar meta", use_container_width=True):
            st.rerun()
    with eliminar:
        if st.button("Eliminar definitivamente", type="primary", use_container_width=True):
            service.eliminar_meta(meta_id)
            st.success("Meta eliminada correctamente.")
            st.rerun()


def mostrar():
    page_header(
        "🎯",
        "Metas inteligentes",
        "Planea viajes, eventos y compras; registra aportes y pagos reales sin duplicar tus gastos.",
        "PLANIFICACION",
    )
    service = GoalService()
    account_service = AccountService()
    category_service = CategoryService()
    try:
        cuentas = account_service.obtener_cuentas()
        categorias_gasto = [categoria for categoria in category_service.obtener_categorias() if categoria.activa and categoria.tipo == "Gasto"]

        with st.expander("➕ Nueva meta", expanded=True):
            with st.form("form_meta", clear_on_submit=True):
                columna_1, columna_2 = st.columns(2)
                with columna_1:
                    nombre = st.text_input("Nombre", placeholder="Ej: Viaje a Cartagena")
                    objetivo = st.number_input("Valor objetivo", min_value=0.01, value=1_000_000.0, step=100_000.0)
                    moneda = st.selectbox("Moneda de la meta", ["COP", "USD"])
                with columna_2:
                    fecha_limite = st.date_input("Fecha objetivo (opcional)", value=None)
                    descripcion = st.text_area("Descripción", placeholder="Ej: Vuelos, hospedaje y actividades")
                crear = st.form_submit_button("Crear meta", use_container_width=True)
                if crear:
                    try:
                        service.crear_meta(nombre, objetivo, moneda, fecha_limite, descripcion)
                        st.success("Meta creada correctamente.")
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))

        metas = service.obtener_metas()
        if not metas:
            st.info("Crea tu primera meta para planificar una compra, viaje o evento.")
            return

        st.divider()
        st.subheader("Tus metas")
        for meta in metas:
            resumen = service.resumen(meta)
            moneda = meta.moneda
            fecha = meta.fecha_limite.strftime("%d/%m/%Y") if meta.fecha_limite else "Sin fecha límite"
            with st.expander(f"🎯 {meta.nombre} · {resumen['porcentaje']:.0f}% pagado", expanded=False):
                st.caption(meta.descripcion or f"Meta con fecha objetivo: {fecha}")
                columna_1, columna_2, columna_3 = st.columns(3)
                columna_1.metric("Objetivo", _dinero(meta.objetivo, moneda))
                columna_2.metric("Pagado", _dinero(resumen["pagado"], moneda))
                columna_3.metric("Pendiente", _dinero(resumen["pendiente"], moneda))
                st.progress(int(resumen["porcentaje"]))
                st.caption(f"Aportes reservados: {_dinero(resumen['aportado'], moneda)} · Fecha objetivo: {fecha}")

                pestaña_aporte, pestaña_pago, pestaña_historial = st.tabs(["Aportar", "Registrar pago", "Historial"])
                with pestaña_aporte:
                    st.caption("El aporte reserva avance para la meta; no crea un gasto ni altera el saldo de una cuenta.")
                    with st.form(f"aporte_meta_{meta.id}", clear_on_submit=True):
                        aporte_fecha = st.date_input("Fecha del aporte", value=date.today(), key=f"aporte_fecha_{meta.id}")
                        aporte_valor = st.number_input("Valor del aporte", min_value=0.01, value=1_000.0, step=1_000.0, key=f"aporte_valor_{meta.id}")
                        aporte_descripcion = st.text_input("Nota", placeholder="Ej: ahorro de esta quincena", key=f"aporte_nota_{meta.id}")
                        if st.form_submit_button("Registrar aporte", use_container_width=True):
                            try:
                                service.aportar(meta.id, aporte_valor, aporte_fecha, aporte_descripcion)
                                st.success("Aporte registrado.")
                                st.rerun()
                            except ValueError as error:
                                st.error(str(error))

                with pestaña_pago:
                    st.caption("El pago crea un gasto real, descuenta la cuenta elegida y queda visible en Movimientos.")
                    if not cuentas or not categorias_gasto:
                        st.warning("Necesitas una cuenta y una categoría de gasto para registrar pagos.")
                    else:
                        cuentas_por_id = {cuenta.id: cuenta for cuenta in cuentas}
                        categorias_por_id = {categoria.id: categoria for categoria in categorias_gasto}
                        with st.form(f"pago_meta_{meta.id}", clear_on_submit=True):
                            pago_columna_1, pago_columna_2 = st.columns(2)
                            with pago_columna_1:
                                pago_fecha = st.date_input("Fecha del pago", value=date.today(), key=f"pago_fecha_{meta.id}")
                                cuenta_id = st.selectbox("Cuenta que pagó", list(cuentas_por_id), format_func=lambda item: f"{cuentas_por_id[item].nombre} ({cuentas_por_id[item].moneda})", key=f"pago_cuenta_{meta.id}")
                                categoria_id = st.selectbox("Categoría del gasto", list(categorias_por_id), format_func=lambda item: f"{categorias_por_id[item].icono} {categorias_por_id[item].nombre}", key=f"pago_categoria_{meta.id}")
                            with pago_columna_2:
                                pago_descripcion = st.text_input("Descripción", placeholder="Ej: Vuelo Medellín - Cartagena", key=f"pago_descripcion_{meta.id}")
                                pago_valor = st.number_input("Valor pagado", min_value=0.01, value=1_000.0, step=1_000.0, key=f"pago_valor_{meta.id}")
                                pago_observaciones = st.text_area("Observaciones", placeholder="Opcional", key=f"pago_observaciones_{meta.id}")
                            if st.form_submit_button("Registrar pago y movimiento", use_container_width=True):
                                try:
                                    service.registrar_pago(meta.id, pago_fecha, cuenta_id, categoria_id, pago_valor, pago_descripcion, pago_observaciones)
                                    st.success("Pago y movimiento registrados correctamente.")
                                    st.rerun()
                                except ValueError as error:
                                    st.error(str(error))

                with pestaña_historial:
                    if not resumen["operaciones"]:
                        st.info("Aún no hay aportes ni pagos para esta meta.")
                    for operacion in resumen["operaciones"]:
                        simbolo = "💸" if operacion.tipo == "Pago" else "🏦"
                        with st.container(border=True):
                            detalle, accion = st.columns([5, 1])
                            with detalle:
                                st.markdown(f"**{simbolo} {operacion.tipo} · {_dinero(operacion.valor_meta, moneda)}**")
                                st.caption(f"{operacion.fecha.strftime('%d/%m/%Y')} · {operacion.descripcion or 'Sin nota adicional.'}")
                                if operacion.movimiento:
                                    st.caption(f"Movimiento #{operacion.movimiento.id}: {operacion.movimiento.descripcion}")
                            with accion:
                                if st.button("Eliminar", key=f"eliminar_operacion_meta_{operacion.id}", use_container_width=True):
                                    confirm_delete(
                                        "¿Eliminar operación de meta?",
                                        f"{operacion.tipo} · {_dinero(operacion.valor_meta, moneda)}",
                                        "Si es un pago, también se eliminará su movimiento y se restaurará el saldo de la cuenta.",
                                        lambda: service.eliminar_operacion(operacion.id),
                                        "Operación eliminada y saldo restaurado si era un pago.",
                                    )

                accion_archivar, accion_eliminar = st.columns(2)
                with accion_archivar:
                    if st.button("Archivar meta", key=f"archivar_meta_{meta.id}", use_container_width=True):
                        service.desactivar_meta(meta.id)
                        st.success("Meta archivada.")
                        st.rerun()
                with accion_eliminar:
                    if st.button("Eliminar meta y operaciones", key=f"eliminar_meta_{meta.id}", use_container_width=True):
                        aportes = sum(operacion.tipo == "Aporte" for operacion in resumen["operaciones"])
                        pagos = sum(operacion.tipo == "Pago" for operacion in resumen["operaciones"])
                        confirmar_eliminacion(service, meta.id, meta.nombre, aportes, pagos)
    finally:
        service.cerrar()
        account_service.cerrar()
        category_service.cerrar()
