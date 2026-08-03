from datetime import date

import pandas as pd
import streamlit as st

from components.cards import metric_card
from components.ui.page import page_header
from core.services import ReportService


MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def _dinero(valor):
    return f"COP ${valor:,.2f}"


def mostrar():
    page_header("📑", "Reportes", "Consulta tu actividad mensual y exporta archivos listos para analizar o compartir.", "ANÁLISIS")
    hoy = date.today()
    col_mes, col_anio = st.columns(2)
    mes = col_mes.selectbox("Mes", range(1, 13), index=hoy.month - 1, format_func=lambda numero: MESES[numero - 1])
    anio = col_anio.number_input("Año", min_value=2000, max_value=2100, value=hoy.year, step=1)

    service = ReportService()
    try:
        reporte = service.obtener_reporte(int(anio), mes)
        columnas = st.columns(3)
        with columnas[0]:
            metric_card("Ingresos", _dinero(reporte["ingresos_cop"]), "⬆️")
        with columnas[1]:
            metric_card("Gastos", _dinero(reporte["gastos_cop"]), "⬇️")
        with columnas[2]:
            metric_card("Balance", _dinero(reporte["balance_cop"]), "⚖️")

        if reporte["monedas_sin_tasa"]:
            st.warning("Faltan tasas hacia COP para: " + ", ".join(reporte["monedas_sin_tasa"]) + ". Esos movimientos aparecen en el detalle, pero no en los totales.")

        st.subheader("Movimientos del período")
        if not reporte["filas"]:
            st.info("No hay ingresos ni gastos registrados para este período.")
        else:
            vista = pd.DataFrame(reporte["filas"])[["fecha", "tipo", "descripcion", "categoria", "cuenta", "moneda", "valor_original", "valor_cop"]]
            vista.columns = ["Fecha", "Tipo", "Descripción", "Categoría", "Cuenta", "Moneda", "Valor original", "Valor COP"]
            st.dataframe(vista, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("Descargas")
        st.caption("Los archivos Excel y PDF se generan únicamente cuando los preparas, para conservar la velocidad de la aplicación.")
        clave = f"reporte_archivos_{anio}_{mes}"
        if st.button("⚡ Preparar archivos", type="primary", use_container_width=True):
            with st.spinner("Preparando reporte..."):
                st.session_state[clave] = {
                    "csv": service.generar_csv(reporte),
                    "xlsx": service.generar_excel(reporte),
                    "pdf": service.generar_pdf(reporte),
                }

        archivos = st.session_state.get(clave)
        if archivos:
            nombre = f"financeos_{anio}_{mes:02d}"
            col_csv, col_excel, col_pdf = st.columns(3)
            col_csv.download_button("Descargar CSV", archivos["csv"], f"{nombre}.csv", "text/csv", use_container_width=True)
            col_excel.download_button("Descargar Excel", archivos["xlsx"], f"{nombre}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            col_pdf.download_button("Descargar PDF", archivos["pdf"], f"{nombre}.pdf", "application/pdf", use_container_width=True)
    finally:
        service.cerrar()
