import logging
import os

import requests
import streamlit as st

from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
API = os.getenv("API_BASE_URL", "http://localhost:4000")

st.title("Advisor Dashboard")
try:
    resp = requests.get(f"{API}/adv/dashboards/kpis", timeout=10)
    if resp.status_code == 200:
        kpi = resp.json()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Students", kpi.get("totalStudents", 0))
        c2.metric("Total Outreach", kpi.get("totalOutreach", 0))
        c3.metric("Total Placements", kpi.get("totalPlacements", 0))
        c4.metric("Response Rate", kpi.get("responseRate", 0))
    else:
        st.error(f"Could not load advisor KPIs: {resp.text}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running on http://localhost:4000")
