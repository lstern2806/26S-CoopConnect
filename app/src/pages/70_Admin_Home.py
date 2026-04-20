"""Admin Dashboard — KPIs and interactive charts."""

import logging
import os
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

from modules.nav import PAGE_ICON, SideBarLinks

logger = logging.getLogger(__name__)

API = os.getenv("API_BASE_URL", "http://localhost:4000")


def api_request(method: str, url: str, **kwargs):
    return requests.request(method, url, timeout=10, **kwargs)


def api_error_banner(exc: requests.exceptions.RequestException):
    st.error(f"Error connecting to the API: {exc}")
    st.caption("Ensure the API server is running (default: http://localhost:4000).")


st.set_page_config(layout="wide", page_icon=PAGE_ICON)
SideBarLinks()

st.title("Admin Dashboard")
st.caption("High-level platform health, role mix, audit activity, and student distributions.")

try:
    resp = api_request("GET", f"{API}/admin/dashboards/admin-kpis")
    if resp.status_code != 200:
        st.error(f"Could not load admin KPIs: {resp.text}")
    else:
        kpi = resp.json()

        with st.container(border=True):
            st.subheader("Key metrics")
            cols = st.columns(6)
            cols[0].metric("Users", kpi.get("totalUsers", 0))
            cols[1].metric("Active", kpi.get("activeUsers", 0))
            cols[2].metric("Suspended", kpi.get("suspendedUsers", 0))
            cols[3].metric("Advisors", kpi.get("totalAdvisors", 0))
            cols[4].metric("Students", kpi.get("totalStudents", 0))
            cols[5].metric("Employers", kpi.get("totalEmployers", 0))
            row2 = st.columns(2)
            row2[0].metric("Audit log entries", kpi.get("totalAuditLogs", 0))
            row2[1].metric("System settings", kpi.get("totalSystemSettings", 0))

        adv = float(kpi.get("totalAdvisors") or 0)
        stu = float(kpi.get("totalStudents") or 0)
        emp = float(kpi.get("totalEmployers") or 0)
        active_u = float(kpi.get("activeUsers") or 0)
        susp_u = float(kpi.get("suspendedUsers") or 0)

        role_df = pd.DataFrame(
            {"Role": ["Advisor", "Student", "Employer"], "Count": [adv, stu, emp]}
        )
        status_df = pd.DataFrame(
            {"Status": ["Active", "Suspended"], "Count": [active_u, susp_u]}
        )

        if role_df["Count"].sum() > 0:
            fig_roles = px.pie(
                role_df,
                names="Role",
                values="Count",
                hole=0.45,
                title="Role distribution (subtype rows)",
            )
            fig_roles.update_traces(textposition="inside", textinfo="percent+label")
        else:
            fig_roles = None

        if status_df["Count"].sum() > 0:
            fig_status = px.pie(
                status_df,
                names="Status",
                values="Count",
                hole=0.45,
                title="Account status (all users)",
            )
            fig_status.update_traces(textposition="inside", textinfo="percent+label")
        else:
            fig_status = None

        st.divider()
        st.subheader("Overview charts")
        with st.container(border=True):
            c1, c2 = st.columns(2)
            with c1:
                if fig_roles:
                    st.plotly_chart(fig_roles, use_container_width=True)
                else:
                    st.info("No advisor/student/employer rows to chart.")
            with c2:
                if fig_status:
                    st.plotly_chart(fig_status, use_container_width=True)
                else:
                    st.info("No user status counts to chart.")

        audit_resp = api_request("GET", f"{API}/admin/dashboards/audit-activity")
        if audit_resp.status_code == 200:
            audit_rows = audit_resp.json()
            if audit_rows:
                adf = pd.DataFrame(audit_rows)
                date_col = "activityDate" if "activityDate" in adf.columns else adf.columns[0]
                adf["day"] = pd.to_datetime(adf[date_col]).dt.date
                cnt_col = "cnt" if "cnt" in adf.columns else adf.columns[-1]
                last30 = [date.today() - timedelta(days=d) for d in range(29, -1, -1)]
                full = pd.DataFrame({"day": last30})
                counts = adf.groupby("day", as_index=False)[cnt_col].sum()
                merged = full.merge(counts, on="day", how="left").fillna({cnt_col: 0})
                with st.container(border=True):
                    fig_audit = px.line(
                        merged,
                        x="day",
                        y=cnt_col,
                        markers=True,
                        title="Audit activity (last 30 days)",
                        labels={"day": "Date", cnt_col: "Actions"},
                    )
                    fig_audit.update_layout(hovermode="x unified")
                    st.plotly_chart(fig_audit, use_container_width=True)
            else:
                st.info("No audit log activity in the last 30 days.")
        else:
            st.warning(f"Audit activity chart unavailable: {audit_resp.text}")

        stats_resp = api_request("GET", f"{API}/admin/dashboards/student-stats")
        if stats_resp.status_code == 200:
            stats = stats_resp.json()
            gpa_dist = stats.get("gpaDistribution") or []
            yr_dist = stats.get("gradYearDistribution") or []
            with st.container(border=True):
                gc1, gc2 = st.columns(2)
                with gc1:
                    if gpa_dist:
                        gdf = pd.DataFrame(gpa_dist)
                        fig_gpa = px.bar(
                            gdf,
                            x="gpaBucket",
                            y="studentCount",
                            title="Students by GPA band",
                            labels={"gpaBucket": "GPA band", "studentCount": "Students"},
                        )
                        st.plotly_chart(fig_gpa, use_container_width=True)
                    else:
                        st.info("No student GPA data.")
                with gc2:
                    if yr_dist:
                        ydf = pd.DataFrame(yr_dist)
                        fig_y = px.bar(
                            ydf,
                            x="gradYear",
                            y="studentCount",
                            title="Students by graduation year",
                            labels={"gradYear": "Grad year", "studentCount": "Students"},
                        )
                        st.plotly_chart(fig_y, use_container_width=True)
                    else:
                        st.info("No graduation year data.")
        else:
            st.warning(f"Student stats unavailable: {stats_resp.text}")

except requests.exceptions.RequestException as e:
    api_error_banner(e)
