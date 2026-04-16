import logging

import requests
import streamlit as st

from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
API = "http://localhost:4000"

st.title("Advisor Students")
col1, col2 = st.columns(2)
major = col1.text_input("Major filter")
experience_level = col2.text_input("Experience level filter")

params = {}
if major:
    params["major"] = major
if experience_level:
    params["experience_level"] = experience_level

try:
    resp = requests.get(f"{API}/adv/students", params=params, timeout=10)
    if resp.status_code == 200:
        st.dataframe(resp.json(), use_container_width=True)
    else:
        st.error(f"Could not load students: {resp.text}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running on http://localhost:4000")
