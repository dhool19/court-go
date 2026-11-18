from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from components.booking_dialogs import reschedule_booking_dialog
from components.layout import page_header
from services.api import APIError, api_request
from services.auth import require_login

CENTRE_TIMEZONE = ZoneInfo("Europe/Berlin")


def local_datetime(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
        CENTRE_TIMEZONE
    )


def is_upcoming(booking, current_time):
    return (
        booking["status"] == "confirmed"
        and local_datetime(booking["starts_at"]) > current_time
    )


def render():
    user = require_login()
    is_admin = user.get("role") == "admin"

    page_header(
        "All bookings" if is_admin else "My bookings",
        "Manage upcoming games and view your booking history.",
    )

    try:
        bookings = api_request(
            "GET",
            "/bookings",
            protected=True,
        )
    except APIError as error:
        st.error(str(error))
        return

    if not bookings:
        st.info("No bookings yet.")

        st.page_link(
            "views/courts.py",
            label="Explore courts",
        )
        return

    current_time = datetime.now(CENTRE_TIMEZONE)

    upcoming = [booking for booking in bookings if is_upcoming(booking, current_time)]

    left, right = st.columns(2)

    left.metric("Upcoming games", len(upcoming))
    right.metric("Total bookings", len(bookings))

    selected_view = st.radio(
        "Show bookings",
        options=["Upcoming", "History", "All"],
        horizontal=True,
    )

    if selected_view == "Upcoming":
        visible_bookings = upcoming

    elif selected_view == "History":
        visible_bookings = [
            booking for booking in bookings if not is_upcoming(booking, current_time)
        ]

    else:
        visible_bookings = bookings

    visible_bookings = sorted(
        visible_bookings,
        key=lambda booking: local_datetime(booking["starts_at"]),
        reverse=selected_view != "Upcoming",
    )

    st.caption("All times are shown in Europe/Berlin.")

    if not visible_bookings:
        st.info("No bookings in this view.")
        return

    for booking in visible_bookings:
        booking_id = booking["id"]

        starts_at = local_datetime(booking["starts_at"])
        ends_at = local_datetime(booking["ends_at"])

        with st.container(border=True):
            st.caption(f"BOOKING #{booking_id} · " f"{booking['status'].upper()}")

            st.subheader(booking["court_name"])

            if is_admin:
                st.write(
                    f"**Booked by:** "
                    f"{(booking.get('customer_name') or 'Name unavailable').title()}"
                )

            st.write(f"**Sport:** " f"{booking.get('sport_type', 'Unknown').title()}")

            date_column, time_column, price_column = st.columns(3)

            date_column.write("**Date**")
            date_column.write(f"{starts_at:%d %b %Y}")

            time_column.write("**Time**")
            time_column.write(f"{starts_at:%H:%M} - {ends_at:%H:%M}")

            price_column.write("**Price**")
            price_column.write(f"€{float(booking['booked_price']):.2f}")

            if is_upcoming(booking, current_time):
                st.divider()

                if st.button(
                    "Reschedule",
                    key=f"reschedule_{booking_id}",
                ):
                    reschedule_booking_dialog(booking)

                with st.expander("Cancel this booking"):
                    confirmed = st.checkbox(
                        "I confirm I want to cancel this booking.",
                        key=f"confirm_cancel_{booking_id}",
                    )

                    cancel_clicked = st.button(
                        "Cancel booking",
                        key=f"cancel_{booking_id}",
                        disabled=not confirmed,
                    )

                    if cancel_clicked:
                        try:
                            api_request(
                                "POST",
                                f"/bookings/{booking_id}/cancel",
                                protected=True,
                            )
                        except APIError as error:
                            st.error(str(error))
                        else:
                            st.session_state.flash_message = (
                                f"Booking #{booking_id} cancelled."
                            )

                            st.rerun()


render()
