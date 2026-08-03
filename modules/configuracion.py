from datetime import datetime

import streamlit as st

from components.cards import metric_card
from components.ui.page import page_header
from core.services import BackupService


def _tamano(bytes_):
    if bytes_ < 1024 * 1024:
        return f"{bytes_ / 1024:,.1f} KB"
    return f"{bytes_ / (1024 * 1024):,.1f} MB"


@st.dialog("🛡️ Restaurar respaldo")
def confirmar_restauracion(contenido, nombre):
    st.markdown("## ¿Restaurar todos los datos?")
    st.caption(nombre)
    st.warning("Se reemplazarán cuentas, movimientos, categorías, metas, inversiones y demás datos actuales. Antes se guardará automáticamente una copia de seguridad.")
    confirmacion = st.text_input("Escribe RESTAURAR para continuar", placeholder="RESTAURAR")
    cancelar, restaurar = st.columns(2)
    if cancelar.button("Cancelar", use_container_width=True):
        st.rerun()
    if restaurar.button("Restaurar respaldo", type="primary", use_container_width=True, disabled=confirmacion != "RESTAURAR"):
        service = BackupService()
        try:
            seguridad = service.restaurar(contenido)
            st.cache_data.clear()
            st.cache_resource.clear()
            st.success(f"Restauración completada. Copia anterior guardada en {seguridad.name}.")
            st.session_state.pop("respaldo_preparado", None)
            st.rerun()
        except ValueError as error:
            st.error(str(error))


def mostrar():
    page_header("⚙️", "Configuración", "Protege tus datos y consulta el estado de tu instalación de FinanceOS.", "SISTEMA")
    service = BackupService()
    estado = service.estado()

    columnas = st.columns(3)
    with columnas[0]:
        metric_card("Motor de datos", estado["motor"].upper(), "🗄️")
    with columnas[1]:
        metric_card("Tamaño local", _tamano(estado["tamano"]), "💾")
    with columnas[2]:
        actualizado = estado["modificado"].strftime("%d/%m/%Y %H:%M") if estado["modificado"] else "Sin datos"
        metric_card("Último cambio", actualizado, "🕒")

    st.subheader("Copia de seguridad")
    st.caption("El respaldo incluye la base financiera y los comprobantes almacenados localmente.")
    if not service.disponible:
        st.info("Cuando migremos a PostgreSQL, los respaldos se administrarán desde el servidor.")
        return

    if st.button("⚡ Preparar respaldo", type="primary", use_container_width=True):
        with st.spinner("Creando una copia consistente..."):
            st.session_state["respaldo_preparado"] = service.crear_respaldo()

    respaldo = st.session_state.get("respaldo_preparado")
    if respaldo:
        nombre = f"financeos_respaldo_{datetime.now():%Y%m%d_%H%M}.zip"
        st.download_button("⬇️ Descargar respaldo", respaldo, nombre, "application/zip", use_container_width=True)
        st.caption(f"Archivo preparado: {_tamano(len(respaldo))}")

    st.divider()
    st.subheader("Restaurar datos")
    st.caption("Selecciona únicamente un respaldo ZIP creado por FinanceOS.")
    archivo = st.file_uploader("Archivo de respaldo", type=["zip"], label_visibility="collapsed")
    if archivo and st.button("Revisar y restaurar", use_container_width=True):
        confirmar_restauracion(archivo.getvalue(), archivo.name)
