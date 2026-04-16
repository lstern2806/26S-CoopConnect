import logging

import pandas as pd
import requests
import streamlit as st

from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
API = "http://localhost:4000"

st.title("Advisor Placements")

try:
    placements_resp = requests.get(f"{API}/adv/placements", timeout=10)
    if placements_resp.status_code == 200:
        st.subheader("Placement Records")
        st.dataframe(placements_resp.json(), use_container_width=True)
    else:
        st.error(f"Could not load placements: {placements_resp.text}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running on http://localhost:4000")

try:
    trends_resp = requests.get(f"{API}/adv/placements/trends", timeout=10)
    if trends_resp.status_code == 200:
        st.subheader("Placement Trends")
        trends = trends_resp.json()
        st.dataframe(trends, use_container_width=True)
        if trends and "companyName" in trends[0] and "totalPlacements" in trends[0]:
            df = pd.DataFrame(trends)
            st.bar_chart(df.set_index("companyName")["totalPlacements"])
    else:
        st.error(f"Could not load trends: {trends_resp.text}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running on http://localhost:4000")
