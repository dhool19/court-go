import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.title("CourtGo")


# ==========================================
# 1. ADD COURT DIALOG
# ==========================================
@st.dialog("Add a new Court")
def add_court_dialog():
    with st.form("add_court"):
        name = st.text_input("Court Name", max_chars=100)
        sport_type = st.selectbox("Sport", ["badminton", "tennis", "football"])
        hourly_price = st.number_input(
            "Hourly Price (€)", min_value=0.01, value=20, step=5, format="%.2f"
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
                response = requests.post(f"{API_URL}/courts", json=payload, timeout=5)
                response.raise_for_status()
            except requests.RequestException as error:
                st.error(f"Could not save the court. {error}")
            else:
                st.success(f"Added {name.strip()}!")
                st.rerun()


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
            min_value=0.0,
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
            response = requests.delete(f"{API_URL}/courts/{court['id']}", timeout=5)
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
            btn_col1, btn_col2 = st.columns(2)

            if btn_col1.button("✏️", key=f"edit_{court['id']}", help="Edit"):
                edit_court_dialog(court)

            if btn_col2.button("🗑️", key=f"del_{court['id']}", help="Delete"):
                delete_court_dialog(court)

st.divider()
