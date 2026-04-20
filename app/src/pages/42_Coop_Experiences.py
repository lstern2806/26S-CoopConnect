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

st.title("Co-op Experiences")

if not student_id:
    st.error("Missing student_id in session. Please log in again from Home.")
    st.stop()

st.subheader("Browse All Experiences")
col1, col2, col3 = st.columns(3)
company = col1.text_input("Company")
industry = col2.text_input("Industry")
role = col3.text_input("Role")
params = {"company": company, "industry": industry, "role": role}
try:
    browse_resp = requests.get(f"{API}/stu/experiences", params={k: v for k, v in params.items() if v}, timeout=10)
    if browse_resp.status_code == 200:
        st.dataframe(browse_resp.json(), use_container_width=True)
    else:
        st.error(f"Could not load experiences: {browse_resp.text}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running on http://localhost:4000")

st.subheader("My Experience History")
try:
    mine_resp = requests.get(f"{API}/stu/students/{student_id}/experiences", timeout=10)
    if mine_resp.status_code == 200:
        st.dataframe(mine_resp.json(), use_container_width=True)
    else:
        st.error(f"Could not load your experiences: {mine_resp.text}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running on http://localhost:4000")

st.subheader("Add Experience")
with st.form("add_experience"):
    company_id = st.number_input("Company ID", min_value=1, step=1)
    role_id = st.number_input("Role ID", min_value=1, step=1)
    semester = st.selectbox("Semester", ["Spring", "Summer", "Fall"])
    year = st.number_input("Year", min_value=2020, max_value=2035, value=2026, step=1)
    notes = st.text_area("Notes")
    add_submit = st.form_submit_button("Add Experience", type="primary")
    if add_submit:
        payload = {
            "companyId": int(company_id),
            "roleId": int(role_id),
            "semester": semester,
            "year": int(year),
            "notes": notes,
        }
        try:
            add_resp = requests.post(f"{API}/stu/students/{student_id}/experiences", json=payload, timeout=10)
            if add_resp.status_code == 201:
                st.success("Experience added.")
                st.rerun()
            else:
                st.error(f"Add failed: {add_resp.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to the API: {str(e)}")
            st.info("Please ensure the API server is running on http://localhost:4000")

st.subheader("Delete Experience")
experience_id = st.number_input("Experience ID to delete", min_value=1, step=1)
if st.button("Delete Experience"):
    try:
        del_resp = requests.delete(f"{API}/stu/students/{student_id}/experiences/{int(experience_id)}", timeout=10)
        if del_resp.status_code == 200:
            st.success("Experience deleted.")
            st.rerun()
        else:
            st.error(f"Delete failed: {del_resp.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the API: {str(e)}")
        st.info("Please ensure the API server is running on http://localhost:4000")
