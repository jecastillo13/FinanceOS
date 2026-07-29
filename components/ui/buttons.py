import streamlit as st


def icon_button(
    icon,
    key,
    help=None,
    type="secondary"
):

    return st.button(
        icon,
        key=key,
        help=help,
        use_container_width=True,
        type=type
    )