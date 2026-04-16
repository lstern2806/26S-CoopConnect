import logging

import requests
import streamlit as st

from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
API = "http://localhost:4000"

st.title("Advisor Networking Activity")
try:
    resp = requests.get(f"{API}/adv/networking/engagement", timeout=10)
    if resp.status_code == 200:
        st.dataframe(resp.json(), use_container_width=True)
    else:
        st.error(f"Could not load networking metrics: {resp.text}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running on http://localhost:4000")
