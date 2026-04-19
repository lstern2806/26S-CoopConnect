import logging
import os

import requests
import streamlit as st

from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
API = os.getenv("API_BASE_URL", "http://localhost:4000")
student_id = st.session_state.get("student_id")

st.title("My Profile")

if not student_id:
    st.error("Missing student_id in session. Please log in again from Home.")
    st.stop()

try:
    response = requests.get(f"{API}/stu/students/{student_id}", timeout=10)
    if response.status_code == 200:
        profile = response.json()
        st.subheader(f"{profile.get('firstName')} {profile.get('lastName')}")
        col1, col2, col3 = st.columns(3)
        col1.metric("Major", profile.get("major"))
        col2.metric("GPA", profile.get("GPA"))
        col3.metric("Graduation Year", profile.get("gradYear"))
        st.write(f"📧 {profile.get('email')}")

        with st.form("update_profile"):
            major = st.text_input("Major", value=profile.get("major") or "")
            gpa = st.number_input("GPA", min_value=0.0, max_value=4.0, value=float(profile.get("GPA") or 0.0), step=0.1)
            grad_year = st.number_input("Graduation Year", min_value=2025, max_value=2035, value=int(profile.get("gradYear") or 2027), step=1)
            submitted = st.form_submit_button("Update Profile", type="primary")
            if submitted:
                payload = {"major": major, "GPA": gpa, "gradYear": grad_year}
                try:
                    put_resp = requests.put(f"{API}/stu/students/{student_id}", json=payload, timeout=10)
                    if put_resp.status_code == 200:
                        st.success("Profile updated successfully.")
                        st.rerun()
                    else:
                        st.error(f"Update failed: {put_resp.text}")
                except requests.exceptions.RequestException as e:
                    st.error(f"Error connecting to the API: {str(e)}")
                    st.info("Please ensure the API server is running on http://localhost:4000")
    else:
        st.error(f"Unable to load profile: {response.text}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running on http://localhost:4000")
