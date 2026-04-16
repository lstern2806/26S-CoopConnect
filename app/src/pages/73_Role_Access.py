import logging
import os

import requests
import streamlit as st

from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
API = os.getenv("API_BASE_URL", "http://localhost:4000")
admin_id = st.session_state.get("admin_id", 1)

st.title("Role Access")
user_id = st.number_input("User ID", min_value=1, step=1)

if st.button("Load Access Details"):
    try:
        resp = requests.get(f"{API}/admin/users/{int(user_id)}/access", timeout=10)
        if resp.status_code == 200:
            st.json(resp.json())
        else:
            st.error(f"Load failed: {resp.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the API: {str(e)}")
        st.info("Please ensure the API server is running on http://localhost:4000")

role_type = st.selectbox("Role type", ["STUDENT", "ADVISOR", "EMPLOYER"])
department = st.text_input("Advisor department (for ADVISOR)")
advisor_id = st.number_input("Advisor ID (for STUDENT)", min_value=1, step=1)
major = st.text_input("Major (for STUDENT)")
gpa = st.number_input("GPA (for STUDENT)", min_value=0.0, max_value=4.0, value=3.0, step=0.1)
grad_year = st.number_input("Grad year (for STUDENT)", min_value=2025, max_value=2035, value=2027, step=1)
company_id = st.number_input("Company ID (for EMPLOYER)", min_value=1, step=1)
job_title = st.text_input("Job title (for EMPLOYER)")

col1, col2 = st.columns(2)
if col1.button("Assign Role"):
    payload = {"roleType": role_type, "adminId": admin_id}
    if role_type == "ADVISOR":
        payload["department"] = department
    elif role_type == "STUDENT":
        payload.update({"advisorId": int(advisor_id), "major": major, "GPA": gpa, "gradYear": int(grad_year)})
    else:
        payload.update({"companyId": int(company_id), "jobTitle": job_title})
    try:
        resp = requests.post(f"{API}/admin/users/{int(user_id)}/access", json=payload, timeout=10)
        if resp.status_code in [200, 201]:
            st.success("Role assigned.")
        else:
            st.error(f"Assign failed: {resp.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the API: {str(e)}")
        st.info("Please ensure the API server is running on http://localhost:4000")

if col2.button("Revoke Role"):
    try:
        resp = requests.delete(
            f"{API}/admin/users/{int(user_id)}/access",
            params={"roleType": role_type, "adminId": admin_id},
            timeout=10,
        )
        if resp.status_code == 200:
            st.success("Role removed.")
        else:
            st.error(f"Revoke failed: {resp.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the API: {str(e)}")
        st.info("Please ensure the API server is running on http://localhost:4000")
