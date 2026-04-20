import logging
import os

import requests
import streamlit as st

from modules.nav import PAGE_ICON, SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide", page_icon=PAGE_ICON)
SideBarLinks()
API = os.getenv("API_BASE_URL", "http://localhost:4000")
student_id = st.session_state.get("student_id")

st.title("Student Outreach")

if not student_id:
    st.error("Missing student_id in session. Please log in again from Home.")
    st.stop()

try:
    messages_resp = requests.get(f"{API}/stu/students/{student_id}/outreach", timeout=10)
    if messages_resp.status_code == 200:
        st.dataframe(messages_resp.json(), use_container_width=True)
    else:
        st.error(f"Could not load outreach messages: {messages_resp.text}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running on http://localhost:4000")

with st.form("send_outreach"):
    recipient_id = st.number_input("Recipient Student ID", min_value=1, step=1)
    content = st.text_area("Message")
    submitted = st.form_submit_button("Send Outreach", type="primary")
    if submitted:
        payload = {"recipientId": int(recipient_id), "content": content}
        try:
            send_resp = requests.post(f"{API}/stu/students/{student_id}/outreach", json=payload, timeout=10)
            if send_resp.status_code == 201:
                st.success("Outreach sent.")
                st.rerun()
            else:
                st.error(f"Send failed: {send_resp.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to the API: {str(e)}")
            st.info("Please ensure the API server is running on http://localhost:4000")
