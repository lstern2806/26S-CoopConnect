"""Audit Logs — searchable, filterable log viewer with export (admin)."""

import logging
from datetime import date, timedelta

import pandas as pd
import requests
import streamlit as st

from modules.api import API_BASE_URL as API
from modules.api import api_error_banner, api_request, response_error_message
from modules.nav import PAGE_ICON, SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide", page_icon=PAGE_ICON)
SideBarLinks()

st.title("Audit Logs")
st.caption("Browse, filter, and export platform audit records.")

ROWS_PER_PAGE = 25

try:
    logs_resp = api_request("GET", f"{API}/admin/audit-logs")
    if logs_resp.status_code == 200:
        all_logs = logs_resp.json()
        if all_logs:
            df = pd.DataFrame(all_logs)

            if "actionTimestamp" in df.columns:
                df["actionTimestamp"] = pd.to_datetime(df["actionTimestamp"])
                df["_date"] = df["actionTimestamp"].dt.date
            else:
                df["_date"] = None

            st.subheader("Filters")
            fc1, fc2, fc3 = st.columns(3)

            action_types = sorted(df["actionType"].dropna().unique().tolist()) if "actionType" in df.columns else []
            selected_type = fc1.selectbox("Action type", ["All"] + action_types, key="audit_action_filter")

            today = date.today()
            default_start = today - timedelta(days=30)
            date_range = fc2.date_input(
                "Date range",
                value=(default_start, today),
                key="audit_date_range",
            )

            search_q = fc3.text_input("Search details", key="audit_search")

            filtered = df.copy()

            if selected_type != "All" and "actionType" in filtered.columns:
                filtered = filtered[filtered["actionType"] == selected_type]

            if isinstance(date_range, (list, tuple)) and len(date_range) == 2 and filtered["_date"].notna().any():
                d_start, d_end = date_range
                filtered = filtered[(filtered["_date"] >= d_start) & (filtered["_date"] <= d_end)]

            if search_q and "actionDetails" in filtered.columns:
                filtered = filtered[filtered["actionDetails"].str.contains(search_q, case=False, na=False)]

            display_cols = [c for c in filtered.columns if not c.startswith("_")]
            filtered_display = filtered[display_cols].reset_index(drop=True)

            total_rows = len(filtered_display)
            total_pages = max(1, (total_rows + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE)

            st.divider()
            st.subheader("Audit Log Records")
            st.caption(f"Showing **{total_rows}** record(s)")

            page_num = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1, key="audit_page")
            start_idx = (page_num - 1) * ROWS_PER_PAGE
            end_idx = min(start_idx + ROWS_PER_PAGE, total_rows)

            st.dataframe(
                filtered_display.iloc[start_idx:end_idx],
                use_container_width=True,
                hide_index=True,
            )
            st.caption(f"Page {page_num} of {total_pages}")

        else:
            st.info("No audit log records found.")
    else:
        st.error(f"Could not load logs: {response_error_message(logs_resp)}")
except requests.exceptions.RequestException as e:
    api_error_banner(e)

st.divider()

try:
    summary_resp = api_request("GET", f"{API}/admin/audit-logs/summary")
    if summary_resp.status_code == 200:
        summary = summary_resp.json()
        st.subheader("Audit Summary")
        st.dataframe(summary, use_container_width=True)
        if summary and isinstance(summary, list) and len(summary) > 0:
            first = summary[0]
            if isinstance(first, dict) and "actionType" in first and "totalActions" in first:
                sdf = pd.DataFrame(summary)
                st.bar_chart(sdf.set_index("actionType")["totalActions"])
    else:
        st.error(f"Could not load summary: {response_error_message(summary_resp)}")
except requests.exceptions.RequestException as e:
    api_error_banner(e)
