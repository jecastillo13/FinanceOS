import streamlit as st

from core.services import CategoryService


def mostrar():

    st.title("🏷 Gestión de Categorías")
    st.caption("Administra las categorías de ingresos y gastos.")

    service = CategoryService()

    try:

        categorias = service.obtener_categorias()

        total = len(categorias)
        ingresos = len([c for c in categorias if c.tipo == "Ingreso"])
        gastos = len([c for c in categorias if c.tipo == "Gasto"])

        c1, c2, c3 = st.columns(3)

        c1.metric("Total", total)
        c2.metric("Ingresos", ingresos)
        c3.metric("Gastos", gastos)

        st.divider()

        st.subheader("➕ Nueva categoría")

        with st.form("form_categoria", clear_on_submit=True):

            nombre = st.text_input(
                "Nombre",
                placeholder="Ej: Alimentación"
            )

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

            guardar = st.form_submit_button(
                "Guardar categoría",
                use_container_width=True
            )

            if guardar:

                if nombre.strip():

                    service.crear_categoria(
                        nombre,
                        tipo,
                        color
                    )

                    st.success("Categoría creada correctamente.")
                    st.rerun()

                else:

                    st.error("Debes escribir un nombre.")

        st.divider()

        st.subheader("📋 Categorías registradas")

        buscar = st.text_input(
            "🔍 Buscar categoría"
        )

        if buscar:

            categorias = [
                c for c in categorias
                if buscar.lower() in c.nombre.lower()
            ]

        if not categorias:

            st.info("Todavía no existen categorías.")
            return

        for categoria in categorias:

            col1, col2, col3, col4 = st.columns([5, 2, 1, 1])

            col1.markdown(
                f"<span style='color:{categoria.color};font-size:20px;'>●</span> "
                f"**{categoria.nombre}**",
                unsafe_allow_html=True
            )

            col2.write(categoria.tipo)

            if col3.button(
                "✏️",
                key=f"editar_{categoria.id}"
            ):
                st.info("La edición se implementará en el siguiente paso.")

            if col4.button(
                "🗑",
                key=f"eliminar_{categoria.id}"
            ):

                eliminado = service.eliminar_categoria(
                    categoria.id
                )

                if eliminado:

                    st.success("Categoría eliminada.")
                    st.rerun()

                else:

                    st.error(
                        "No se puede eliminar porque tiene movimientos asociados."
                    )

    finally:

        service.cerrar()