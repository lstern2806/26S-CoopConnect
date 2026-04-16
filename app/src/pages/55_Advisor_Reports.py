import logging
import os

import requests
import streamlit as st

from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
API = os.getenv("API_BASE_URL", "http://localhost:4000")
advisor_id = st.session_state.get("advisor_id")

st.title("Advisor Reports")

if not advisor_id:
    st.error("Missing advisor_id in session. Please log in again from Home.")
    st.stop()

try:
    resp = requests.get(f"{API}/adv/dashboards/reports/{advisor_id}", timeout=10)
    if resp.status_code == 200:
        st.dataframe(resp.json(), use_container_width=True)
    else:
        st.error(f"Could not load reports: {resp.text}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running on http://localhost:4000")

with st.form("create_report"):
    new_name = st.text_input("New report name")
    create_submit = st.form_submit_button("Create Report", type="primary")
    if create_submit and new_name:
        try:
            create_resp = requests.post(
                f"{API}/adv/dashboards/reports",
                json={"advisorId": advisor_id, "reportName": new_name},
                timeout=10,
            )
            if create_resp.status_code == 201:
                st.success("Report created.")
                st.rerun()
            else:
                st.error(f"Create failed: {create_resp.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to the API: {str(e)}")
            st.info("Please ensure the API server is running on http://localhost:4000")

report_id = st.number_input("Report ID", min_value=1, step=1)
new_report_name = st.text_input("Rename report to")
col1, col2 = st.columns(2)
if col1.button("Rename Report"):
    try:
        rename_resp = requests.put(
            f"{API}/adv/dashboards/reports/{int(report_id)}",
            json={"reportName": new_report_name},
            timeout=10,
        )
        if rename_resp.status_code == 200:
            st.success("Report renamed.")
            st.rerun()
        else:
            st.error(f"Rename failed: {rename_resp.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the API: {str(e)}")
        st.info("Please ensure the API server is running on http://localhost:4000")

if col2.button("Delete Report"):
    try:
        delete_resp = requests.delete(f"{API}/adv/dashboards/reports/{int(report_id)}", timeout=10)
        if delete_resp.status_code == 200:
            st.success("Report deleted.")
            st.rerun()
        else:
            st.error(f"Delete failed: {delete_resp.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the API: {str(e)}")
        st.info("Please ensure the API server is running on http://localhost:4000")
