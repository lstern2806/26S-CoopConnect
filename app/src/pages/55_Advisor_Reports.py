import logging
import os
import requests
import streamlit as st
from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
API = os.getenv("API_BASE_URL", "http://localhost:4000")

advisor_id = st.session_state.get("advisor_id")

st.title("Reports")

if not advisor_id:
    st.error("Missing advisor_id")
    st.stop()

try:
    resp = requests.get(
        f"{API}/adv/advisors/reports",
        params={"advisorId": advisor_id}
    )

    if resp.status_code == 200:
        reports = resp.json()

        for r in reports:
            st.markdown(f"### {r['reportName']}")
            st.write(f"Created: {r['createdAt']}")
            st.divider()

    else:
        st.error("Could not load reports")

except:
    st.error("API error")
