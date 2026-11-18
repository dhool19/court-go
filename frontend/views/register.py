import streamlit as st

from components.layout import page_header
from services.api import APIError, api_request


def render():
    _, center, _ = st.columns([1, 2, 1])

    with center:
        page_header("Create your account", "Join CourtGo and make time for your game.")

    with st.form("register_form"):
        left, right = st.columns(2)

        first_name = left.text_input("First name", max_chars=100)
        last_name = right.text_input("Last name", max_chars=100)
        email = st.text_input("Email", placeholder="johnsmith@gmail.com")
        password = st.text_input(
            "Password", type="password", help="Use at least 8 characters"
        )
        confirm_password = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button(
            "Create account", type="primary", use_container_width=True
        )

        if submitted:
            if not first_name.strip() or not last_name.strip():
                st.error("Enter your first name or last name.")
            elif len(password) > 8:
                st.error("Password must contain atleast 8 characters.")
            elif confirm_password != password:
                st.error("Password do not match.")
            elif (
                "@" not in email
                or not email.split("@")[0].strip()
                or "." not in email.rsplit("@", 1)[-1]
            ):
                st.error("Enter a valid email address.")
            else:
                try:
                    api_request(
                        "POST",
                        "/auth/register",
                        json={
                            "first_name": first_name.strip(),
                            "last_name": last_name.strip(),
                            "email": email.strip(),
                            "password": password,
                        },
                    )
                except APIError as e:
                    st.error(str(e))

                else:
                    st.session_state.flash_message = (
                        "Account created successfully. Please log in."
                    )

                    st.switch_page("views/login.py")

        st.divider()

        st.page_link(
            "views/login.py",
            label="Already have an account? Log in",
        )


render()
