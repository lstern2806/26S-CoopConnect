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

        st.subheader("Overview")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Students", kpi.get("totalStudents", 0))
        col2.metric("Outreach", kpi.get("totalOutreach", 0))
        col3.metric("Placements", kpi.get("totalPlacements", 0))
        col4.metric("Response Rate", f"{kpi.get('responseRate', 0)*100:.0f}%")

        st.divider()

        st.subheader("Insights")

        if kpi.get("responseRate", 0) < 0.3:
            st.warning("Low response rate → students may need networking support")

        if kpi.get("totalPlacements", 0) < 2:
            st.info("Placement activity is low → review student pipeline")

    else:
        st.error("Could not load advisor KPIs")

except:
    st.error("API connection error")
