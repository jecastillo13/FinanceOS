import streamlit as st


def metric_card(
    title: str,
    value,
    icon: str = "",
    help_text: str = "",
):

    help_markup = f'<div class="metric-help">{help_text}</div>' if help_text else ""
    st.markdown(
        f'''<div class="metric-card">
            <div class="metric-top"><span>{title}</span><span class="metric-icon">{icon}</span></div>
            <div class="metric-value">{value}</div>{help_markup}
        </div>''',
        unsafe_allow_html=True,
    )
