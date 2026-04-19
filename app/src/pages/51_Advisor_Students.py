import logging
import os
import requests
import streamlit as st
from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
API = os.getenv("API_BASE_URL", "http://localhost:4000")

st.title("Students Overview")

try:
    resp = requests.get(f"{API}/adv/students", timeout=10)

    if resp.status_code == 200:
        students = resp.json()

        for s in students:
            with st.container():
                st.markdown(f"### {s['firstName']} {s['lastName']}")
                col1, col2 = st.columns(2)

                col1.write(f"Major: {s['major']}")
                col2.write(f"GPA: {s['GPA']}")

                st.divider()

    else:
        st.error("Could not load students")

except:
    st.error("API error")
