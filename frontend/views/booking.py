from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import streamlit as st

from components.layout import page_header
from services.api import APIError, api_request

CENTRE_TIMEZONE = ZoneInfo("Europe/Berlin")


def local_datetime(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
        CENTRE_TIMEZONE
    )


def slot_label(slot):
    starts_at = local_datetime(slot["starts_at"])
    ends_at = local_datetime(slot["ends_at"])

    return f"{starts_at:%H:%M} - {ends_at:%H:%M}"


def slot_status(slot, current_time):
    if slot["is_blocked"]:
        return "Maintenance"

    if slot["is_booked"]:
        return "Booked"

    if local_datetime(slot["starts_at"]) <= current_time:
        return "Past"

    return "Available"


def render():
    page_header(
        "Book a court",
        "Choose your court, date, and preferred time.",
    )

    try:
        courts = api_request("GET", "/courts")
    except APIError as error:
        st.error(str(error))
        return

    if not courts:
        st.info("No courts available yet.")
        return

    courts_by_id = {court["id"]: court for court in courts}

    court_ids = list(courts_by_id)

    preferred_id = st.session_state.pop(
        "preferred_court_id",
        None,
    )

    if preferred_id in courts_by_id:
        st.session_state.booking_court_id = preferred_id

    if st.session_state.get("booking_court_id") not in courts_by_id:
        st.session_state.booking_court_id = court_ids[0]

    left, right = st.columns(2)

    selected_court_id = left.selectbox(
        "Court",
        options=court_ids,
        format_func=lambda court_id: (
            f"{courts_by_id[court_id]['name']} · "
            f"{courts_by_id[court_id]['sport_type'].title()}"
        ),
        key="booking_court_id",
    )

    today = datetime.now(CENTRE_TIMEZONE).date()
    latest_date = today + timedelta(days=30)

    stored_date = st.session_state.get("booking_date")

    if stored_date is None or stored_date < today or stored_date > latest_date:
        st.session_state.booking_date = today

    selected_date = right.date_input(
        "Date",
        min_value=today,
        max_value=latest_date,
        key="booking_date",
    )

    court = courts_by_id[selected_court_id]

    current_user = st.session_state.get("current_user")

    if current_user and current_user.get("role") == "admin":
        if st.button(
            "Generate slots",
            key="generate_court_slots",
            type="primary",
        ):
            try:
                result = api_request(
                    "POST",
                    f"/courts/{selected_court_id}/slots/generate",
                    protected=True,
                    json={
                        "date": selected_date.isoformat(),
                    },
                )
            except APIError as e:
                st.error(str(e))
            else:
                created_count = result["created_slots"]

                if created_count:
                    st.success(f"Created {created_count} slots.")
                else:
                    st.info(f"Slots already exist for this date.")

    with st.container(border=True):
        st.subheader(court["name"])

        st.write(
            f"{court['sport_type'].title()} · "
            f"€{float(court['hourly_price']):.2f} / hour"
        )

        if court.get("description"):
            st.write(court["description"])

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

    st.subheader("Court availability")
    st.caption("All times are shown in Europe/Berlin.")

    if not slots:
        st.info("No slots generated for this court and date.")
        return

    current_time = datetime.now(CENTRE_TIMEZONE)

    slots = sorted(
        slots,
        key=lambda slot: local_datetime(slot["starts_at"]),
    )

    rows = [
        {
            "Time": slot_label(slot),
            "Status": slot_status(slot, current_time),
        }
        for slot in slots
    ]

    st.dataframe(
        rows,
        hide_index=True,
        use_container_width=True,
    )

    available_slots = {
        slot["id"]: slot
        for slot in slots
        if slot_status(slot, current_time) == "Available"
    }

    if not available_slots:
        st.info("Try another court or date for available times.")
        return

    if not st.session_state.get("current_user"):
        st.info("Please log in to confirm a booking.")

        st.page_link(
            "views/login.py",
            label="Go to login",
        )
        return

    with st.form(f"booking_form_{selected_court_id}_{selected_date}"):
        selected_slot_id = st.selectbox(
            "Choose your time",
            options=list(available_slots),
            format_func=lambda slot_id: slot_label(available_slots[slot_id]),
        )

        st.caption("The backend confirms the final price " "and slot availability.")

        submitted = st.form_submit_button(
            "Confirm booking",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        try:
            booking = api_request(
                "POST",
                "/bookings",
                protected=True,
                json={
                    "slot_id": selected_slot_id,
                },
            )
        except APIError as error:
            st.error(str(error))
        else:
            st.session_state.flash_message = f"Booking #{booking['id']} confirmed."

            st.switch_page("views/bookings.py")


render()
