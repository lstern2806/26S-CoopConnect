import logging
import os

import requests
import streamlit as st

from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
API = os.getenv("API_BASE_URL", "http://localhost:4000")
employer_id = st.session_state.get("employer_id")

st.title("Employer Outreach")

if not employer_id:
    st.error("Missing employer_id in session. Please log in again from Home.")
    st.stop()

try:
    messages_resp = requests.get(f"{API}/emp/{employer_id}/outreach/history", timeout=10)
    if messages_resp.status_code == 200:
        st.dataframe(messages_resp.json(), use_container_width=True)
    else:
        st.error(f"Could not load outreach messages: {messages_resp.text}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running on http://localhost:4000")

with st.form("send_outreach"):
    studentId = st.number_input("Recipient Student ID", min_value=1, step=1)
    content = st.text_area("Message")
    submitted = st.form_submit_button("Send Outreach", type="primary")
    if submitted:
        payload = {"studentId": int(studentId), "content": content}
        try:
            send_resp = requests.post(f"{API}/emp/{employer_id}/outreach", json=payload, timeout=10)
            if send_resp.status_code == 201:
                st.success("Outreach sent.")
                st.rerun()
            else:
                st.error(f"Send failed: {send_resp.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to the API: {str(e)}")
            st.info("Please ensure the API server is running on http://localhost:4000")
