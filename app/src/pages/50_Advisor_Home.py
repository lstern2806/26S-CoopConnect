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

st.title("Advisor Dashboard")

# ── Overview KPIs ──────────────────────────────────────────────
try:
    resp = requests.get(f"{API}/adv/dashboards/kpis", timeout=10)

    if resp.status_code == 200:
        kpi = resp.json()

        st.subheader("Overview")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Students", kpi.get("totalStudents", 0))
        col2.metric("Outreach", kpi.get("totalOutreach", 0))
        col3.metric("Placements", kpi.get("totalPlacements", 0))
        rate = float(kpi.get("responseRate") or 0)
        col4.metric("Response Rate", f"{rate*100:.0f}%")

        st.divider()

        st.subheader("Insights")

        has_insight = False

        if rate < 0.3:
            st.warning("Low response rate — students may need networking support")
            has_insight = True

        if kpi.get("totalPlacements", 0) < 2:
            st.info("Placement activity is low — review student pipeline")
            has_insight = True

        if not has_insight:
            st.success("All metrics are looking healthy — no issues detected.")

    else:
        st.error("Could not load advisor KPIs")

except requests.exceptions.RequestException as e:
    st.error(f"API connection error: {e}")

st.divider()

# ── Placements by Industry ─────────────────────────────────────
st.subheader("Placements by Industry")
try:
    perf_resp = requests.get(f"{API}/adv/dashboards/performance", timeout=10)
    if perf_resp.status_code == 200:
        perf_data = perf_resp.json()
        if perf_data:
            df_perf = pd.DataFrame(perf_data)
            st.bar_chart(df_perf.set_index("industry")["placements"])
            with st.expander("View raw data"):
                st.dataframe(df_perf, use_container_width=True)
        else:
            st.info("No placement data available yet.")
    else:
        st.error("Could not load performance data.")
except requests.exceptions.RequestException as e:
    st.error(f"API connection error: {e}")

st.divider()

# ── Top Companies by Placements ────────────────────────────────
st.subheader("Top Companies by Placements")
try:
    trends_resp = requests.get(f"{API}/adv/placements/trends", timeout=10)
    if trends_resp.status_code == 200:
        trends_data = trends_resp.json()
        if trends_data:
            df_trends = pd.DataFrame(trends_data)
            st.bar_chart(df_trends.set_index("companyName")["totalPlacements"])
            with st.expander("View raw data"):
                st.dataframe(df_trends, use_container_width=True)
        else:
            st.info("No placement trends available yet.")
    else:
        st.error("Could not load placement trends.")
except requests.exceptions.RequestException as e:
    st.error(f"API connection error: {e}")

st.divider()

# ── Student Networking Activity ────────────────────────────────
st.subheader("Student Networking Activity")
try:
    net_resp = requests.get(f"{API}/adv/networking-activity", timeout=10)
    if net_resp.status_code == 200:
        net_data = net_resp.json()
        if net_data:
            df_net = pd.DataFrame(net_data)
            df_net["name"] = df_net["firstName"] + " " + df_net["lastName"]
            df_net["responseRate"] = df_net["responseRate"].apply(
                lambda v: float(v or 0)
            )

            chart_df = df_net.set_index("name")[
                ["totalStudentOutreach", "totalEmployerResponses"]
            ]
            chart_df.columns = ["Outreach Sent", "Responses Received"]
            st.bar_chart(chart_df)

            with st.expander("View raw data"):
                st.dataframe(
                    df_net[["name", "totalStudentOutreach", "totalEmployerResponses", "responseRate"]],
                    use_container_width=True,
                )
        else:
            st.info("No networking activity data available yet.")
    else:
        st.error("Could not load networking activity.")
except requests.exceptions.RequestException as e:
    st.error(f"API connection error: {e}")
