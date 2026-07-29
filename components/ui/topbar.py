import streamlit as st


def topbar():

    col1, col2 = st.columns([8, 1])

    with col1:
        st.title("💰 FinanceOS")
        st.caption("Tu centro de control financiero")

    with col2:
        st.write("")
        st.write("")
        st.button(
            "⚙️",
            key="topbar_settings",
            use_container_width=True
        )

    st.divider()