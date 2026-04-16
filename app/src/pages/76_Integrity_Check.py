import logging

import requests
import streamlit as st

from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
API = "http://localhost:4000"

st.title("Integrity Check")
st.write("Users with zero or multiple access roles are listed below.")

try:
    resp = requests.get(f"{API}/admin/integrity/user-role-conflicts", timeout=10)
    if resp.status_code == 200:
        conflicts = resp.json()
        if conflicts:
            st.warning(f"Found {len(conflicts)} role conflicts.")
            st.dataframe(conflicts, use_container_width=True)
        else:
            st.success("No user-role conflicts detected.")
    else:
        st.error(f"Could not run integrity check: {resp.text}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running on http://localhost:4000")
