import streamlit as st


def page_header(icono, titulo, descripcion, etiqueta="FINANCEOS"):
    st.markdown(
        f'''<div class="page-hero">
            <div class="page-hero-icon">{icono}</div>
            <div><div class="page-hero-label">{etiqueta}</div>
            <div class="page-hero-title">{titulo}</div>
            <div class="page-hero-description">{descripcion}</div></div>
        </div>''',
        unsafe_allow_html=True,
    )
