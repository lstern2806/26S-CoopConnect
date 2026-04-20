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

st.title("Employer Messages")

if not student_id:
    st.error("Missing student_id in session. Please log in again from Home.")
    st.stop()

try:
    resp = requests.get(f"{API}/stu/students/{student_id}/employer-outreach", timeout=10)
    if resp.status_code == 200:
        messages = resp.json()
        if not messages:
            st.info("No employer outreach messages.")
        else:
            for msg in messages:
                with st.expander(f"Message #{msg.get('empMessageId')} - {msg.get('companyName')} ({msg.get('status')})"):
                    st.write(msg.get("content"))
                    valid_statuses = ["pending", "accepted", "rejected"]
                    current_status = msg.get("status", "pending")
                    status_idx = valid_statuses.index(current_status) if current_status in valid_statuses else 0
                    status = st.radio(
                        "Update status",
                        valid_statuses,
                        index=status_idx,
                        key=f"status_{msg.get('empMessageId')}",
                        horizontal=True,
                    )
                    if st.button("Save Status", key=f"save_{msg.get('empMessageId')}"):
                        try:
                            update_resp = requests.put(
                                f"{API}/stu/students/{student_id}/employer-outreach/{msg.get('empMessageId')}",
                                json={"status": status},
                                timeout=10,
                            )
                            if update_resp.status_code == 200:
                                st.success("Status updated.")
                                st.rerun()
                            else:
                                st.error(f"Update failed: {update_resp.text}")
                        except requests.exceptions.RequestException as e:
                            st.error(f"Error connecting to the API: {str(e)}")
                            st.info("Please ensure the API server is running on http://localhost:4000")
    else:
        st.error(f"Could not load employer messages: {resp.text}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running on http://localhost:4000")
