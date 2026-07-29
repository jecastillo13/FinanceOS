import streamlit as st


def metric_card(
    title: str,
    value,
    icon: str = "",
    help_text: str = "",
):

    st.container(border=True)

    st.metric(
        label=f"{icon} {title}",
        value=value,
        help=help_text
    )