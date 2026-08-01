import streamlit as st


@st.dialog("⚠️ Confirmar eliminación")
def confirm_delete(title, description, impact, action, success_message, error_message="No fue posible completar la eliminación."):
    """Muestra una confirmación visual antes de una acción destructiva."""
    st.markdown(f"## {title}")
    st.caption(description)
    if impact:
        st.warning(impact)
    cancelar, eliminar = st.columns(2)
    with cancelar:
        if st.button("Cancelar", use_container_width=True):
            st.rerun()
    with eliminar:
        if st.button("Eliminar definitivamente", type="primary", use_container_width=True):
            try:
                eliminado = action()
                if eliminado is False:
                    st.error(error_message)
                    return
                st.success(success_message)
                st.rerun()
            except ValueError as error:
                st.error(str(error))
