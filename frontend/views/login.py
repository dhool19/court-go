import streamlit as st

from components.layout import page_header
from services.api import APIError
from services.auth import login_user


def render():
    _, center, _ = st.columns([1, 2, 1])

    with center:
        page_header(
            "Welcome back",
            "Log in to book your next game.",
        )

        with st.form("login_form"):
            email = st.text_input(
                "Email",
                placeholder="you@example.com",
            )

            password = st.text_input(
                "Password",
                type="password",
            )

            submitted = st.form_submit_button(
                "Log in",
                type="primary",
                use_container_width=True,
            )

        # Outside the form.
        if submitted:
            if not email.strip() or not password:
                st.error("Enter your email and password.")
            else:
                try:
                    login_user(email, password)
                except APIError as error:
                    st.error(str(error))

        st.divider()

        st.page_link(
            "views/register.py",
            label="New to CourtGo? Create an account",
        )


render()
