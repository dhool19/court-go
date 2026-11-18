import extra_streamlit_components as stx
import streamlit as st

from services.api import APIError, api_request

COOKIE_NAME = "courtgo_access_token"


def _get_cookie_manager():
    manager = stx.CookieManager(
        key="courtgo_cookie_reader",
    )

    st.session_state["_cookie_manager"] = manager
    return manager


def initialize_session():
    cookie_manager = _get_cookie_manager()

    if "_auth_initialized" not in st.session_state:
        saved_token = st.context.cookies.get(COOKIE_NAME)

        st.session_state.access_token = (
            saved_token if isinstance(saved_token, str) and saved_token else None
        )

        st.session_state.current_user = None
        st.session_state["_logged_out"] = False
        st.session_state["_auth_initialized"] = True

    action = st.session_state.pop("_auth_cookie_action", None)

    if action == "save":
        token = st.session_state.get("access_token")

        if token:
            cookie_manager.set(
                cookie=COOKIE_NAME,
                val=token,
                key="courtgo_save_login",
                path="/",
                max_age=24 * 60 * 60,
                same_site="strict",
                secure=False,
            )

    elif action == "delete":
        cookie_manager.cookies.setdefault(COOKIE_NAME, "")

        cookie_manager.delete(
            COOKIE_NAME,
            key="courtgo_delete_login",
        )

    if "token" in st.query_params:
        del st.query_params["token"]


def login_user(email, password):
    result = api_request(
        "POST",
        "/auth/login",
        json={"email": email.strip(), "password": password},
    )
    if not isinstance(result, dict) or not result.get("access_token"):
        raise APIError("Login response did not contain an access token.")

    st.session_state.access_token = result["access_token"]
    st.session_state.current_user = None
    st.session_state["_logged_out"] = False

    st.session_state["_auth_cookie_action"] = "save"
    st.session_state.flash_message = "Logged in successfully."

    st.rerun()


def load_current_user():
    if not st.session_state.get("access_token"):
        st.session_state.current_user = None
        return None

    user = api_request(
        "GET",
        "/auth/me",
        protected=True,
    )

    st.session_state.current_user = user
    return user


def require_login():
    user = st.session_state.get("current_user")

    if not user:
        st.warning("Please log in to access this page.")
        st.stop()

    return user


def require_admin():
    user = require_login()

    if user.get("role") != "admin":
        st.error("You do not have permission to access this page.")
        st.stop()

    return user


def logout_user():
    st.session_state.access_token = None
    st.session_state.current_user = None
    st.session_state["_logged_out"] = True
    st.session_state["_auth_cookie_action"] = "delete"
    st.session_state.flash_message = "You have been logged out."

    st.query_params.clear()

    st.session_state.pop("_cookie_manager", None)

    st.rerun()
