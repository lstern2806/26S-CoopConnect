import logging

import requests
import streamlit as st

from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
API = "http://localhost:4000"

st.title("Co-op History")
company_id = st.session_state.get("company_id")
if not company_id:
    st.error("Missing company_id in session. Please log in again from Home.")
    st.stop()

try:
    resp = requests.get(f"{API}/emp/students/history", params={"companyId": company_id}, timeout=10)
    if resp.status_code == 200:
        st.dataframe(resp.json(), use_container_width=True)
    else:
        st.error(f"Could not load company co-op history: {resp.text}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running on http://localhost:4000")
