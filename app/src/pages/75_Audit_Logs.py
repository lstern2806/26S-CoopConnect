import logging

import pandas as pd
import requests
import streamlit as st

from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
API = "http://localhost:4000"

st.title("Audit Logs")

try:
    logs_resp = requests.get(f"{API}/admin/audit-logs", timeout=10)
    if logs_resp.status_code == 200:
        st.subheader("Audit Log Records")
        st.dataframe(logs_resp.json(), use_container_width=True)
    else:
        st.error(f"Could not load logs: {logs_resp.text}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running on http://localhost:4000")

try:
    summary_resp = requests.get(f"{API}/admin/audit-logs/summary", timeout=10)
    if summary_resp.status_code == 200:
        summary = summary_resp.json()
        st.subheader("Audit Summary")
        st.dataframe(summary, use_container_width=True)
        if summary and "actionType" in summary[0] and "totalActions" in summary[0]:
            df = pd.DataFrame(summary)
            st.bar_chart(df.set_index("actionType")["totalActions"])
    else:
        st.error(f"Could not load summary: {summary_resp.text}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running on http://localhost:4000")
