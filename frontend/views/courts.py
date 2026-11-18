import streamlit as st
from components.layout import page_header
from services.api import api_request, APIError


def render():
    page_header(
        "Find your next game", "Explore courts, choose your sport, and book your time."
    )

    try:
        courts = api_request("GET", "/courts")
    except APIError as e:
        st.error(str(e))
        return

    if not courts:
        st.info("No courts available yet.")
        return

    sports = sorted(court["sport_type"] for court in courts)
    selected_sport = st.selectbox(
        "Filter by sport",
        options=["All sports"] + sports,
        format_func=lambda sport: sport.title(),
    )

    filter_courts = [
        court
        for court in courts
        if selected_sport == "All sports" or court["sport_type"] == selected_sport
    ]

    st.caption(f"{len(filter_courts)} court(s) found")

    columns = st.columns(2)

    for (
        index,
        court,
    ) in enumerate(filter_courts):
        with columns[index % 2]:
            with st.container(border=True):
                st.caption(court["sport_type"].upper())

                st.subheader(court["name"])

                st.write(court.get("description") or "Ready for your next game.")

                st.markdown(f"**€{float(court['hourly_price']):.2f} / hour**")

                if st.button(
                    "View available times",
                    key=f"view_court_{court['id']}",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state.preferred_court_id = court["id"]
                    st.switch_page("views/booking.py")


render()
