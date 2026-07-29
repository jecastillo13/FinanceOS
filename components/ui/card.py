import streamlit as st


class Card:

    def __enter__(self):

        self.container = st.container(
            border=True
        )

        return self.container

    def __exit__(

        self,

        exc_type,

        exc,

        tb

    ):

        pass