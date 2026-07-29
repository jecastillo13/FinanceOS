import streamlit as st


def load_css():

    st.markdown(
        """
<style>

.block-container{

    padding-top:2rem;

    padding-bottom:2rem;

    max-width:1500px;

}

div[data-testid="stMetric"]{

    background:#1B1F27;

    border-radius:18px;

    padding:18px;

    border:1px solid #30363D;

}

div[data-testid="stMetric"]:hover{

    border:1px solid #4F46E5;

}

div[data-testid="stVerticalBlockBorderWrapper"]{

    border-radius:18px;

}

</style>
""",
        unsafe_allow_html=True
    )