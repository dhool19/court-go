import streamlit as st


def apply_styles():
    st.markdown(
        """
        <style>
            .stApp {
                background-color: #F5F7FA;
            }

            .block-container {
                max-width: 1150px;
                padding-top: 2.5rem;
                padding-bottom: 3rem;
            }

            h1, h2, h3 {
                color: #173B35;
                letter-spacing: -0.03em;
            }

            [data-testid="stSidebar"] {
                background-color: #FFFFFF;
                border-right: 1px solid #E5EAE8;
            }

            [data-testid="stForm"] {
                background-color: #FFFFFF;
                padding: 1.5rem;
                border: 1px solid #E5EAE8;
                border-radius: 16px;
            }

            [data-testid="stMetric"] {
                background-color: #FFFFFF;
                padding: 1rem;
                border: 1px solid #E5EAE8;
                border-radius: 14px;
            }

            button[kind="primary"] {
                background-color: #157D63;
                border-color: #157D63;
                color: #FFFFFF;
                border-radius: 10px;
            }

            button[kind="primary"]:hover {
                background-color: #10654F;
                border-color: #10654F;
                color: #FFFFFF;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title, subtitle=None):
    st.title(title)

    if subtitle:
        st.caption(subtitle)


def show_flash_message():
    message = st.session_state.pop("flash_message", None)

    if message:
        st.info(message)
