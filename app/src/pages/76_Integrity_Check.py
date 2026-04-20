"""Integrity Check — accounts with zero or multiple access roles."""

import logging

import pandas as pd
import requests
import streamlit as st

from modules.api import API_BASE_URL as API
from modules.api import api_error_banner, api_request, response_error_message
from modules.nav import PAGE_ICON, SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide", page_icon=PAGE_ICON)
SideBarLinks()

st.title("Integrity Check")
st.caption(
    "Lists users who have **no** access role or **more than one** role across ADMIN / ADVISOR / STUDENT / EMPLOYER."
)

try:
    resp = api_request("GET", f"{API}/admin/integrity/user-role-conflicts")
    if resp.status_code != 200:
        st.error(f"Could not run integrity check: {response_error_message(resp)}")
    else:
        conflicts = resp.json()
        if not conflicts:
            st.success("No user-role conflicts detected.")
        else:
            df = pd.DataFrame(conflicts)
            df["Conflict type"] = df.apply(
                lambda r: (
                    "No Role Assigned"
                    if (r.get("role_count") or 0) == 0
                    else f"Multiple Roles: {r.get('roles') or '(tags missing)'}"
                ),
                axis=1,
            )
            df["Indicator"] = df["role_count"].apply(
                lambda c: "No role" if c == 0 else "Multiple roles"
            )

            no_role = int((df["role_count"] == 0).sum())
            multi = int((df["role_count"] > 1).sum())

            st.divider()
            m1, m2, m3 = st.columns(3)
            m1.metric("Conflicts found", len(df))
            m2.metric("No role assigned", no_role, help="User has no ADMIN/ADVISOR/STUDENT/EMPLOYER row.")
            m3.metric("Multiple roles", multi, help="User has more than one role subtype.")

            display_cols = [
                "userId",
                "firstName",
                "lastName",
                "email",
                "roles",
                "role_count",
                "Conflict type",
                "Indicator",
            ]
            for c in display_cols:
                if c not in df.columns:
                    df[c] = ""
            st.subheader("Conflicting accounts")
            st.dataframe(
                df[display_cols],
                use_container_width=True,
                hide_index=True,
                height=min(420, 40 + len(df) * 35),
            )

            st.divider()
            st.subheader("Fix in Role Access")
            uid_options = sorted(df["userId"].astype(int).tolist())
            _row_by_uid = {
                int(r["userId"]): r for _, r in df.iterrows()
            }

            def _fmt_uid(uid) -> str:
                key = int(uid)
                r = _row_by_uid.get(key)
                if r is None:
                    return str(key)
                ct = r.get("Conflict type", "")
                return f"{key} — {r.get('firstName', '')} {r.get('lastName', '')} ({ct})"

            pick = st.selectbox(
                "Choose a User ID to open in Role Access",
                uid_options,
                format_func=_fmt_uid,
            )
            if st.button("Open Role Access for this user", type="primary"):
                st.session_state["prefill_role_access_user_id"] = int(pick)
                st.switch_page("pages/73_Role_Access.py")

except requests.exceptions.RequestException as e:
    api_error_banner(e)
