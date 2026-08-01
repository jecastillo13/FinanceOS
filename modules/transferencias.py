from datetime import date

import streamlit as st

from core.services import AccountService, TransferService
from components.ui.page import page_header


def mostrar():
    page_header("🔄", "Transferencias", "Mueve dinero entre cuentas sin afectar tus ingresos ni gastos.", "OPERACIONES")
    transfer_service = TransferService()
    account_service = AccountService()

    try:
        cuentas = account_service.obtener_cuentas()
        if len(cuentas) < 2:
            st.warning("Necesitas al menos dos cuentas para realizar una transferencia.")
            return

        cuentas_por_id = {cuenta.id: cuenta for cuenta in cuentas}
        cuenta_ids = list(cuentas_por_id)
        with st.form("nueva_transferencia", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                fecha = st.date_input("Fecha", value=date.today())
                origen_id = st.selectbox("Cuenta de origen", cuenta_ids, format_func=lambda item: f"{cuentas_por_id[item].nombre} ({cuentas_por_id[item].moneda})")
                valor = st.number_input("Valor", min_value=0.01, value=1.0, step=1000.0, format="%.2f")
            with col2:
                destino_id = st.selectbox("Cuenta de destino", cuenta_ids, index=1, format_func=lambda item: f"{cuentas_por_id[item].nombre} ({cuentas_por_id[item].moneda})")
                descripcion = st.text_input("Descripción", placeholder="Ej: Ahorro mensual")

            if st.form_submit_button("Transferir", use_container_width=True):
                try:
                    transfer_service.crear_transferencia(fecha, origen_id, destino_id, valor, descripcion)
                    st.success("Transferencia registrada. Los saldos fueron actualizados.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))

        st.divider()
        st.subheader("Historial de transferencias")
        transferencias = transfer_service.obtener_transferencias()
        if not transferencias:
            st.info("Todavía no hay transferencias registradas.")
            return

        for transferencia in transferencias:
            with st.expander(
                f"{transferencia.fecha.strftime('%d/%m/%Y')} · {transferencia.cuenta_origen.nombre} → {transferencia.cuenta_destino.nombre} · ${transferencia.valor:,.2f}"
            ):
                st.write(f"**Origen:** {transferencia.cuenta_origen.nombre}")
                st.write(f"**Destino:** {transferencia.cuenta_destino.nombre}")
                if transferencia.descripcion:
                    st.caption(transferencia.descripcion)
                if st.button("Revertir transferencia", key=f"revertir_transferencia_{transferencia.id}"):
                    transfer_service.eliminar_transferencia(transferencia.id)
                    st.success("Transferencia revertida y saldos restaurados.")
                    st.rerun()
    finally:
        transfer_service.cerrar()
        account_service.cerrar()
