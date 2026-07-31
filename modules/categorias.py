import streamlit as st

from core.services import CategoryService


TIPOS = ["Ingreso", "Gasto", "Transferencia", "Ahorro", "Inversion"]


def mostrar():
    st.title("🏷️ Gestión de categorías")
    st.caption("Organiza tus movimientos por tipo, grupo, icono y prioridad.")
    service = CategoryService()

    try:
        categorias = service.obtener_categorias()
        ingresos = len([c for c in categorias if c.tipo == "Ingreso"])
        gastos = len([c for c in categorias if c.tipo == "Gasto"])
        especiales = len(categorias) - ingresos - gastos
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", len(categorias))
        c2.metric("Ingresos", ingresos)
        c3.metric("Gastos", gastos)
        c4.metric("Especiales", especiales)

        if st.button("Instalar catálogo predeterminado"):
            creadas = service.instalar_categorias_predeterminadas()
            if creadas:
                st.success(f"Se instalaron {creadas} categorías predeterminadas.")
                st.rerun()
            else:
                st.info("El catálogo ya estaba instalado; no se crearon duplicados.")

        st.divider()
        with st.expander("➕ Nueva categoría", expanded=True):
            with st.form("form_categoria", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    nombre = st.text_input("Nombre", placeholder="Ej: Alimentación")
                    tipo = st.selectbox("Tipo", TIPOS)
                    grupo = st.text_input("Grupo", value="Otros", placeholder="Ej: Alimentación")
                with col2:
                    icono = st.text_input("Icono", value="🏷️", max_chars=10)
                    color = st.color_picker("Color", "#2196F3")
                    orden = st.number_input("Orden", min_value=0, value=0, step=1)
                if st.form_submit_button("Guardar categoría", use_container_width=True):
                    if not nombre.strip():
                        st.error("Debes escribir un nombre.")
                    else:
                        service.crear_categoria(nombre, tipo, color, icono or "🏷️", grupo.strip() or "Otros", orden=orden)
                        st.success("Categoría creada correctamente.")
                        st.rerun()

        st.divider()
        buscar = st.text_input("🔍 Buscar categoría, grupo o tipo")
        if buscar:
            texto = buscar.lower()
            categorias = [c for c in categorias if texto in c.nombre.lower() or texto in (c.grupo or "").lower() or texto in c.tipo.lower()]
        if not categorias:
            st.info("No hay categorías para mostrar.")
            return

        grupo_actual = None
        for categoria in categorias:
            encabezado = f"{categoria.tipo} · {categoria.grupo or 'Otros'}"
            if encabezado != grupo_actual:
                st.subheader(encabezado)
                grupo_actual = encabezado
            estado = "Activa" if categoria.activa else "Inactiva"
            sistema = " · Sistema" if categoria.es_sistema else ""
            with st.expander(f"{categoria.icono or '🏷️'} {categoria.nombre} · {estado}{sistema}"):
                with st.form(f"editar_categoria_{categoria.id}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        nombre_editado = st.text_input("Nombre", value=categoria.nombre, key=f"nombre_{categoria.id}")
                        tipo_editado = st.selectbox("Tipo", TIPOS, index=TIPOS.index(categoria.tipo) if categoria.tipo in TIPOS else 0, key=f"tipo_{categoria.id}")
                        grupo_editado = st.text_input("Grupo", value=categoria.grupo or "Otros", key=f"grupo_{categoria.id}")
                    with col2:
                        icono_editado = st.text_input("Icono", value=categoria.icono or "🏷️", max_chars=10, key=f"icono_{categoria.id}")
                        color_editado = st.color_picker("Color", value=categoria.color or "#2196F3", key=f"color_{categoria.id}")
                        activa_editada = st.checkbox("Activa", value=bool(categoria.activa), key=f"activa_{categoria.id}")
                        orden_editado = st.number_input("Orden", min_value=0, value=categoria.orden or 0, step=1, key=f"orden_{categoria.id}")
                    if st.form_submit_button("Guardar cambios"):
                        try:
                            service.actualizar_categoria(categoria.id, nombre_editado.strip(), tipo_editado, color_editado, icono_editado or "🏷️", grupo_editado.strip() or "Otros", activa_editada, orden_editado)
                            st.success("Categoría actualizada.")
                            st.rerun()
                        except ValueError as error:
                            st.error(str(error))

                if st.button("Eliminar categoría", key=f"eliminar_{categoria.id}"):
                    if service.eliminar_categoria(categoria.id):
                        st.success("Categoría eliminada.")
                        st.rerun()
                    else:
                        st.error("No se puede eliminar porque tiene movimientos asociados.")
    finally:
        service.cerrar()
