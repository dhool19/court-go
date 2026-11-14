import requests
import streamlit as st

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

API_URL = "http://localhost:8000"

if "access_token" not in st.session_state:
    st.session_state.access_token = None

st.title("CourtGo")

# ==========================================
# Login User
# ==========================================
if st.session_state.access_token is None:
    with st.sidebar.form("login_form"):
        st.subheader("Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        login_clicked = st.form_submit_button("Login")

    if login_clicked:
        try:
            response = requests.post(
                f"{API_URL}/auth/login",
                json={"email": email, "password": password},
                timeout=5,
            )
            response.raise_for_status()
        except requests.HTTPError:
            st.sidebar.error("Login failed. Check your credentials.")
        except requests.RequestException:
            st.sidebar.error("Could not connect to backend")
        else:
            st.session_state.access_token = response.json()["access_token"]
            st.rerun()

current_user = None
auth_headers = {}

if st.session_state.access_token:
    auth_headers = {"Authorization": f"Bearer {st.session_state.access_token}"}

    try:
        response = requests.get(f"{API_URL}/auth/me", headers=auth_headers, timeout=5)
        response.raise_for_status()
    except requests.HTTPError:
        if response.status_code in (401, 403):
            st.session_state.access_token = None
            st.rerun()
        st.sidebar.error("Could not load your profile.")
    except requests.RequestException:
        st.sidebar.error("Could not connect to Backend")
    else:
        current_user = response.json()
        st.sidebar.write(f"Hello, {current_user["first_name"]}")
        st.sidebar.write(f"Role: {current_user["role"]}")

    if st.sidebar.button("Logout"):
        st.session_state.access_token = None
        st.rerun()

is_admin = current_user is not None and current_user["role"] == "admin"


# ==========================================
# 1. ADD COURT DIALOG
# ==========================================
@st.dialog("Add a new Court")
def add_court_dialog():
    with st.form("add_court"):
        name = st.text_input("Court Name", max_chars=100)
        sport_type = st.selectbox("Sport", ["badminton", "tennis", "football"])
        hourly_price = st.number_input(
            "Hourly Price (€)", min_value=0.01, value=20.0, step=5.0, format="%.2f"
        )
        description = st.text_input("Description (Optional)", max_chars=500)
        submitted = st.form_submit_button("Save Court")

    if submitted:
        if not name.strip():
            st.error("Enter a court name")
        else:
            payload = {
                "name": name.strip(),
                "sport_type": sport_type,
                "hourly_price": f"{hourly_price:.2f}",
                "description": description.strip() or None,
            }

            try:
                response = requests.post(
                    f"{API_URL}/courts", json=payload, headers=auth_headers, timeout=5
                )
                response.raise_for_status()
            except requests.RequestException as error:
                st.error(f"Could not save the court. {error}")
            else:
                st.success(f"Added {name.strip()}!")
                st.rerun()


if is_admin:
    if st.button("Add a new court", type="primary"):
        add_court_dialog()

st.divider()


# ==========================================
# 2. UPDATE COURT DIALOG
# ==========================================
@st.dialog("Edit Court")
def edit_court_dialog(court):
    with st.form("edit_court"):
        name = st.text_input("Court name", value=court["name"], max_chars=100)
        sport_option = ["badminton", "tennis", "football"]
        sport_index = (
            sport_option.index(court["sport_type"])
            if court["sport_type"] in sport_option
            else 0
        )
        sport_type = st.selectbox("Sport", sport_option, index=sport_index)

        hourly_price = st.number_input(
            "Hourly Price (€)",
            min_value=0.01,
            step=5.0,
            format="%.2f",
            value=float(court["hourly_price"]),
        )
        existing_desc = court.get("description")
        if existing_desc is None:
            existing_desc = ""

        description = st.text_input(
            "Description (Optional)", value=str(existing_desc), max_chars=500
        )
        submitted = st.form_submit_button("Update Court")

        if submitted:
            if not name.strip():
                st.error("Enter court name")
            else:
                payload = {
                    "name": name.strip(),
                    "sport_type": sport_type,
                    "hourly_price": f"{hourly_price:.2f}",
                    "description": description.strip() or None,
                }

                try:
                    response = requests.patch(
                        f"{API_URL}/courts/{court['id']}",
                        json=payload,
                        headers=auth_headers,
                        timeout=5,
                    )
                    response.raise_for_status()
                except requests.RequestException as e:
                    st.error(f"Could not updated court: {e}")
                else:
                    st.success(f"Updated {name.strip()}!")
                    st.rerun()
    return


# ==========================================
# 3. DELETE COURT DIALOG
# ==========================================
@st.dialog("Delete Court")
def delete_court_dialog(court):
    st.write(f"Delete {court['name']}?")
    if st.button("Confirm delete", type="primary"):
        try:
            response = requests.delete(
                f"{API_URL}/courts/{court['id']}", headers=auth_headers, timeout=5
            )
            response.raise_for_status()
        except requests.RequestException as e:
            st.error(f"Failed to delete: {e}")
        else:
            st.rerun()


# ==========================================
# 4. LIST COURTS WITH ACTION BUTTONS
# ==========================================

st.subheader("Sports court")

try:
    response = requests.get(f"{API_URL}/courts", timeout=5)
    response.raise_for_status()
    courts = response.json()

except requests.RequestException:
    st.error("Could not load courts.")
    st.stop()

if not courts:
    st.info("No court added yet. Click to add above to add one!")
else:
    col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 3, 2])
    col1.write("**Name**")
    col2.write("**Sport Type**")
    col3.write("**Hourly Price**")
    col4.write("**Description**")
    col5.write("**Actions**")
    st.divider()

    for court in courts:
        (
            col1,
            col2,
            col3,
            col4,
            col5,
        ) = st.columns([3, 2, 2, 3, 2])

        col1.write(court["name"])
        col2.write(court["sport_type"])
        col3.write(court["hourly_price"])
        col4.write(court["description"] or "-")

        with col5:
            if is_admin:
                btn_col1, btn_col2 = st.columns(2)

                if btn_col1.button("✏️", key=f"edit_{court['id']}", help="Edit"):
                    edit_court_dialog(court)

                if btn_col2.button("🗑️", key=f"del_{court['id']}", help="Delete"):
                    delete_court_dialog(court)

st.divider()
st.subheader("View court slots")

centre_timezone = ZoneInfo("Europe/Berlin")
today = datetime.now(centre_timezone).date()

if courts:
    court_option = {court["id"]: court["name"] for court in courts}

    selected_court_id = st.selectbox(
        "Choose a court",
        options=list(court_option),
        format_func=lambda court_id: (f"{court_option[court_id]} (ID: {court_id})"),
    )

    selected_date = st.date_input(
        "Choose a date",
        value=today,
        min_value=today,
        max_value=today + timedelta(days=30),
    )

    if is_admin:
        if st.button("Generate slots", type="primary"):
            try:
                generate_response = requests.post(
                    f"{API_URL}/courts/{selected_court_id}/slots/generate",
                    json={"date": selected_date.isoformat()},
                    headers=auth_headers,
                    timeout=10,
                )

                generate_response.raise_for_status()
            except requests.HTTPError:
                st.error(
                    f"Could not generate slots"
                    f"(HTTP {generate_response.status_code})."
                )
                st.write(generate_response.text)
            except requests.RequestException:
                st.error("Could not connect to backend")

            else:
                created_count = generate_response.json()["created_slots"]

                if created_count:
                    st.success(f"Created {created_count} slots.")
                else:
                    st.error("No new slots needed.")

    try:
        response = requests.get(
            f"{API_URL}/courts/{selected_court_id}/slots",
            params={"selected_date": selected_date.isoformat()},
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        st.error(f"Could not load slots. {error}")
    else:
        slots = response.json()

        if not slots:
            st.info("No slots generated for this date")
        else:
            rows = []

            for slot in slots:
                starts_at = datetime.fromisoformat(
                    slot["starts_at"].replace("Z", "+00:00")
                ).astimezone(centre_timezone)

                ends_at = datetime.fromisoformat(
                    slot["ends_at"].replace("Z", "+00:00")
                ).astimezone(centre_timezone)

                rows.append(
                    {
                        "Slot ID": slot["id"],
                        "Start": starts_at.strftime("%H:%M"),
                        "End": ends_at.strftime("%H:%M"),
                        "Maintenance": ("Blocked" if slot["is_blocked"] else "Open"),
                    }
                )
            st.caption("Times shown in Europe/Berlin.")
            st.dataframe(rows, hide_index=True)
else:
    st.info("Add a court to view its slots.")
