import logging
import os
import requests
import streamlit as st
from modules.nav import SideBarLinks

st.set_page_config(layout="wide")
SideBarLinks()

API = os.getenv("API_BASE_URL", "http://localhost:4000")
company_id = st.session_state.get("company_id")

st.title("Manage Co-op Roles")
st.write("Add new positions to allow students to link their experience reports to specific roles.")

if not company_id:
    st.error("Missing company_id. Please log in again.")
    st.stop()

# --- Form to Add New Role ---
with st.form("new_role_form", clear_on_submit=True):
    st.subheader("Create New Role")
    col1, col2 = st.columns(2)
    
    with col1:
        title = st.text_input("Job Title", placeholder="e.g. Software Engineering Intern")
        dept = st.text_input("Department", placeholder="e.g. Infrastructure")
    
    with col2:
        salary = st.number_input("Hourly Salary ($)", min_value=0.0, step=1.0)
        duration = st.text_input("Duration", placeholder="e.g. 4 Months, Summer 2026")

    submitted = st.form_submit_button("Create Role", type="primary")

    if submitted:
        if not title or not dept:
            st.warning("Please fill in the Job Title and Department.")
        else:
            payload = {
                "companyId": company_id,
                "title": title,
                "department": dept,
                "salary": salary,
                "duration": duration
            }
            try:
                resp = requests.post(f"{API}/emp/roles/create", json=payload)
                if resp.status_code == 201:
                    st.success(f"Successfully created role: {title}")
                else:
                    st.error(f"Failed to create role: {resp.text}")
            except Exception as e:
                st.error(f"Connection error: {e}")

# --- View Existing Roles ---
st.divider()
st.subheader("Current Openings")
try:
    # This uses your existing GET /roles endpoint
    roles_resp = requests.get(f"{API}/emp/roles", params={"companyId": company_id})
    if roles_resp.status_code == 200:
        roles_data = roles_resp.json()
        if roles_data:
            st.table(roles_data)
        else:
            st.info("No roles created yet.")
except Exception as e:
    st.error(f"Could not load existing roles: {e}")