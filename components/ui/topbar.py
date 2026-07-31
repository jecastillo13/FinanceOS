from datetime import date

import streamlit as st


def topbar():
    hoy = date.today().strftime("%d/%m/%Y")
    st.markdown(
        f'''<div class="app-header">
            <div><div class="app-header-title">FinanceOS</div><div class="app-header-subtitle">Tu centro de control financiero · {hoy}</div></div>
            <div class="app-status">● Sistema activo</div>
        </div>''',
        unsafe_allow_html=True,
    )
