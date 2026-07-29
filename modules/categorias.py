import streamlit as st
import pandas as pd

from core.services import FinanceService


def mostrar():

    st.title("📂 Categorías")
    st.caption("Administra las categorías de ingresos y gastos.")

    service = FinanceService()

    with st.expander("➕ Nueva categoría", expanded=True):

        col1, col2 = st.columns(2)

        with col1:

            nombre = st.text_input(
                "Nombre",
                placeholder="Ej: Alimentación"
            )

        with col2:

            tipo = st.selectbox(
                "Tipo",
                [
                    "Ingreso",
                    "Gasto"
                ]
            )

        color = st.color_picker(
            "Color",
            "#2196F3"
        )

        if st.button(
            "Guardar categoría",
            use_container_width=True
        ):

            if nombre.strip():

                service.crear_categoria(
                    nombre,
                    tipo,
                    color
                )

                st.success("Categoría creada.")

                service.cerrar()

                st.rerun()

            else:

                st.error("Debes escribir un nombre.")

    st.divider()

    categorias = service.obtener_categorias()

    if categorias:

        datos = []

        for c in categorias:

            datos.append(
                {
                    "Nombre": c.nombre,
                    "Tipo": c.tipo,
                    "Color": c.color
                }
            )

        df = pd.DataFrame(datos)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info("Todavía no existen categorías.")

    service.cerrar()