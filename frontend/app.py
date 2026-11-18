import streamlit as st

from components.layout import (
    apply_styles,
    show_flash_message,
)
from services.api import APIError
from services.auth import (
    initialize_session,
    load_current_user,
    logout_user,
)

st.set_page_config(
    page_title="CourtGo",
    page_icon="🎾",
    layout="wide",
    initial_sidebar_state="expanded",
)

initialize_session()
apply_styles()


try:
    current_user = load_current_user()

except APIError as error:
    st.error(str(error))

    if st.button("Try again"):
        st.rerun()

    if st.button("Clear session and return to login"):
        logout_user()

    st.stop()


navigation = {
    "Play": [
        st.Page(
            "views/courts.py",
            title="Explore courts",
            icon="🎾",
            default=True,
        ),
        st.Page(
            "views/booking.py",
            title="Book a court",
            icon="📅",
        ),
    ],
}


if current_user:
    booking_title = (
        "All bookings" if current_user.get("role") == "admin" else "My bookings"
    )

    navigation["Account"] = [
        st.Page(
            "views/bookings.py",
            title=booking_title,
            icon="🎟️",
        ),
    ]

else:
    navigation["Account"] = [
        st.Page(
            "views/login.py",
            title="Log in",
            icon="🔐",
        ),
        st.Page(
            "views/register.py",
            title="Create account",
            icon="📝",
        ),
    ]


page = st.navigation(navigation)


with st.sidebar:

    st.markdown("### 🎾 CourtGo")
    st.caption("Make time for your game.")

    if current_user:
        st.write(f"Hello, {(current_user.get('first_name', 'Player')).title()}")

        st.caption(f"Role: {current_user.get('role', 'user').title()}")

        if st.button(
            "Log out",
            use_container_width=True,
        ):
            logout_user()


show_flash_message()
page.run()
