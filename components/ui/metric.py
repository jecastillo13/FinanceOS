import streamlit as st


def metric_card(
    titulo,
    valor,
    icono
):

    with st.container(border=True):

        st.caption(
            f"{icono} {titulo}"
        )

        st.markdown(
            f"## {valor}"
        )