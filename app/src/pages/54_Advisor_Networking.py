import logging
import os
import requests
import streamlit as st
import pandas as pd

from modules.nav import PAGE_ICON, SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide", page_icon=PAGE_ICON)
SideBarLinks()
API = os.getenv("API_BASE_URL", "http://localhost:4000")

st.title("Networking Activity")

try:
    resp = requests.get(f"{API}/adv/networking-activity", timeout=10)

    if resp.status_code == 200:
        data = resp.json()

        if data:
            df = pd.DataFrame(data)

            st.subheader("Response Rate by Student")

            df["responseRate"] = df["totalEmployerResponses"] / df["totalStudentOutreach"].replace(0, 1)

            st.bar_chart(df.set_index("firstName")["responseRate"])

        else:
            st.info("No networking data available")

    else:
        st.error("Could not load networking data")

except:
    st.error("API error")
