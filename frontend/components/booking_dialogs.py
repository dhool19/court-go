from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import streamlit as st

from services.api import APIError, api_request
from services.auth import require_login

CENTRE_TIMEZONE = ZoneInfo("Europe/Berlin")


def local_datetime(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
        CENTRE_TIMEZONE
    )


@st.dialog("Reschedule booking")
def reschedule_booking_dialog(booking):
    require_login()

    st.write(f"**Booking #{booking['id']} · " f"{booking['court_name']}**")

    try:
        courts = api_request("GET", "/courts")
    except APIError as error:
        st.error(str(error))
        return

    if not courts:
        st.info("No courts available.")
        return

    courts_by_id = {court["id"]: court for court in courts}

    court_ids = list(courts_by_id)
    booking_id = booking["id"]

    selected_court_id = st.selectbox(
        "Choose a court",
        options=court_ids,
        format_func=lambda court_id: (
            f"{courts_by_id[court_id]['name']} · "
            f"{courts_by_id[court_id]['sport_type'].title()}"
        ),
        key=f"reschedule_court_{booking_id}",
    )

    today = datetime.now(CENTRE_TIMEZONE).date()

    selected_date = st.date_input(
        "Choose a date",
        value=today,
        min_value=today,
        max_value=today + timedelta(days=30),
        key=f"reschedule_date_{booking_id}",
    )

    try:
        slots = api_request(
            "GET",
            f"/courts/{selected_court_id}/slots",
            params={
                "selected_date": selected_date.isoformat(),
            },
        )
    except APIError as error:
        st.error(str(error))
        return

    current_time = datetime.now(CENTRE_TIMEZONE)

    available_slots = {
        slot["id"]: slot
        for slot in sorted(
            slots,
            key=lambda item: local_datetime(item["starts_at"]),
        )
        if not slot["is_blocked"]
        and not slot["is_booked"]
        and local_datetime(slot["starts_at"]) > current_time
    }

    if not available_slots:
        st.info("No available slots. Try another date or court.")
        return

    def format_slot(slot_id):
        slot = available_slots[slot_id]
        starts_at = local_datetime(slot["starts_at"])
        ends_at = local_datetime(slot["ends_at"])

        return f"{starts_at:%H:%M} - {ends_at:%H:%M}"

    selected_slot_id = st.selectbox(
        "Choose a new time",
        options=list(available_slots),
        format_func=format_slot,
        key=(f"reschedule_slot_{booking_id}_" f"{selected_court_id}_{selected_date}"),
    )

    court = courts_by_id[selected_court_id]

    st.caption("All times are shown in Europe/Berlin.")

    st.write(f"**Court rate:** " f"€{float(court['hourly_price']):.2f} / hour")

    st.caption("The backend confirms the final price and availability.")

    if st.button(
        "Confirm reschedule",
        type="primary",
        key=f"confirm_reschedule_{booking_id}",
        use_container_width=True,
    ):
        try:
            api_request(
                "POST",
                f"/bookings/{booking_id}/reschedule",
                protected=True,
                json={
                    "slot_id": selected_slot_id,
                },
            )
        except APIError as error:
            st.error(str(error))
        else:
            st.session_state.flash_message = f"Booking #{booking_id} rescheduled."

            st.rerun()
