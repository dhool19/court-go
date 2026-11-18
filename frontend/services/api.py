import os

import requests
import streamlit as st

API_URL = os.getenv(
    "COURTGO_API_URL",
    "http://localhost:8000",
).rstrip("/")

COOKIE_NAME = "courtgo_access_token"


class APIError(Exception):
    """An API error that can be shown to the user."""


def clear_expired_session():
    cookie_manager = st.session_state.get("_cookie_manager")

    if cookie_manager is not None:
        if cookie_manager.get(COOKIE_NAME) is not None:
            cookie_manager.delete(
                COOKIE_NAME,
                key="courtgo_delete_expired_login",
            )

    st.session_state.access_token = None
    st.session_state.current_user = None

    st.warning("Your session expired. Please log in again.")

    if st.button(
        "Return to login",
        key="return_after_session_expiry",
        type="primary",
    ):
        st.rerun()

    st.stop()


def api_request(method, endpoint, *, protected=False, **kwargs):
    headers = {}

    if protected:
        token = st.session_state.get("access_token")

        if not token:
            raise APIError("Please log in to continue.")

        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.request(
            method=method,
            url=f"{API_URL}{endpoint}",
            headers=headers,
            timeout=10,
            **kwargs,
        )
    except requests.RequestException:
        raise APIError("Could not connect to the backend. Please try again.") from None

    if response.status_code == 401 and protected:
        clear_expired_session()

    if not response.ok:
        try:
            detail = response.json().get(
                "detail",
                "Request failed.",
            )
        except (ValueError, AttributeError):
            detail = "Request failed. Please try again."

        if isinstance(detail, list):
            detail = "; ".join(
                (
                    str(item.get("msg", "Invalid input"))
                    if isinstance(item, dict)
                    else str(item)
                )
                for item in detail
            )

        raise APIError(str(detail))

    if response.status_code == 204 or not response.content:
        return None

    try:
        return response.json()
    except ValueError:
        raise APIError("The backend returned an unexpected response.") from None
