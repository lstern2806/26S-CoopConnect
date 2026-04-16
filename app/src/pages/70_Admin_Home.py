import logging

import requests
import streamlit as st

from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
API = "http://localhost:4000"

st.title("Admin Dashboard")
try:
    resp = requests.get(f"{API}/admin/dashboards/admin-kpis", timeout=10)
    if resp.status_code == 200:
        kpi = resp.json()
        cols = st.columns(6)
        cols[0].metric("Users", kpi.get("totalUsers", 0))
        cols[1].metric("Active", kpi.get("activeUsers", 0))
        cols[2].metric("Suspended", kpi.get("suspendedUsers", 0))
        cols[3].metric("Advisors", kpi.get("totalAdvisors", 0))
        cols[4].metric("Students", kpi.get("totalStudents", 0))
        cols[5].metric("Employers", kpi.get("totalEmployers", 0))
    else:
        st.error(f"Could not load admin KPIs: {resp.text}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running on http://localhost:4000")
