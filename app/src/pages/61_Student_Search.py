import logging

import requests
import streamlit as st

from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
API = "http://localhost:4000"

st.title("Search Students")
gpa_cutoff = st.slider("Minimum GPA", min_value=0.0, max_value=4.0, value=3.5, step=0.1)

try:
    resp = requests.get(f"{API}/emp/students", params={"gpa": gpa_cutoff}, timeout=10)
    if resp.status_code == 200:
        st.dataframe(resp.json(), use_container_width=True)
    else:
        st.error(f"Could not load students: {resp.text}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running on http://localhost:4000")
