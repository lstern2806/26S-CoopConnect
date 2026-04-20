"""User Management — browse, create, update, and delete users (admin)."""

import logging
import os

import pandas as pd
import requests
import streamlit as st

from modules.nav import PAGE_ICON, SideBarLinks

logger = logging.getLogger(__name__)

API = os.getenv("API_BASE_URL", "http://localhost:4000")
admin_id = st.session_state.get("admin_id", 1)


def api_request(method: str, url: str, **kwargs):
    return requests.request(method, url, timeout=10, **kwargs)


def api_error_banner(exc: requests.exceptions.RequestException):
    st.error(f"Error connecting to the API: {exc}")
    st.caption("Ensure the API server is running (default: http://localhost:4000).")


st.set_page_config(layout="wide", page_icon=PAGE_ICON)
SideBarLinks()

st.title("User Management")
st.caption("Search and maintain user accounts. Filter by **User ID**, status, or name/email.")

tab_browse, tab_create, tab_mutate = st.tabs(["Browse users", "Create user", "Update / delete user"])

with tab_browse:
    with st.container(border=True):
        st.subheader("Filters")
        col_id, col_status, col_search = st.columns([1, 1, 2])
        filter_user_id = col_id.number_input(
            "Search by User ID",
            min_value=0,
            step=1,
            value=0,
            help="Enter 0 to show all users (subject to other filters).",
        )
        status = col_status.selectbox("Account status", ["", "active", "suspended"])
        search = col_search.text_input("Search by name or email")

    params = {}
    if filter_user_id and int(filter_user_id) > 0:
        params["userId"] = int(filter_user_id)
    if status:
        params["status"] = status
    if search:
        params["q"] = search

    try:
        list_resp = api_request("GET", f"{API}/admin/users", params=params)
        if list_resp.status_code == 200:
            rows = list_resp.json()
            if rows:
                st.dataframe(
                    pd.DataFrame(rows),
                    use_container_width=True,
                    hide_index=True,
                    height=min(520, 60 + len(rows) * 35),
                )
            else:
                st.info("No users match your filters.")
        else:
            st.error(f"Could not load users: {list_resp.text}")
    except requests.exceptions.RequestException as e:
        api_error_banner(e)

with tab_create:
    with st.container(border=True):
        st.subheader("Create user")
        with st.form("create_user"):
            first = st.text_input("First name")
            last = st.text_input("Last name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            account_status = st.selectbox("Status", ["active", "suspended"])
            create_submit = st.form_submit_button("Create user", type="primary")
            if create_submit:
                payload = {
                    "firstName": first,
                    "lastName": last,
                    "email": email,
                    "password": password,
                    "accountStatus": account_status,
                    "adminId": admin_id,
                }
                try:
                    resp = api_request("POST", f"{API}/admin/users", json=payload)
                    if resp.status_code == 201:
                        st.success("User created.")
                        st.rerun()
                    else:
                        st.error(f"Create failed: {resp.text}")
                except requests.exceptions.RequestException as e:
                    api_error_banner(e)

with tab_mutate:
    with st.container(border=True):
        st.subheader("Update or delete user")
        target_id = st.number_input("Target User ID", min_value=1, step=1)
        new_first = st.text_input("New first name (optional)")
        new_last = st.text_input("New last name (optional)")
        new_email = st.text_input("New email (optional)")
        new_status = st.selectbox("New status (optional)", ["", "active", "suspended"])
        colu1, colu2 = st.columns(2)
        if colu1.button("Update user"):
            payload = {"adminId": admin_id}
            if new_first:
                payload["firstName"] = new_first
            if new_last:
                payload["lastName"] = new_last
            if new_email:
                payload["email"] = new_email
            if new_status:
                payload["accountStatus"] = new_status
            try:
                resp = api_request(
                    "PUT",
                    f"{API}/admin/users/{int(target_id)}",
                    json=payload,
                )
                if resp.status_code == 200:
                    st.success("User updated.")
                    st.rerun()
                else:
                    st.error(f"Update failed: {resp.text}")
            except requests.exceptions.RequestException as e:
                api_error_banner(e)

        if colu2.button("Delete user"):
            try:
                tid = int(target_id)
                access_resp = api_request("GET", f"{API}/admin/users/{tid}/access")
                if access_resp.status_code == 200:
                    access_data = access_resp.json()
                    role_map = [
                        ("advisor", "ADVISOR"),
                        ("student", "STUDENT"),
                        ("employer", "EMPLOYER"),
                    ]
                    revoke_failed = False
                    for key, role_type in role_map:
                        if access_data.get(key):
                            rev = api_request(
                                "DELETE",
                                f"{API}/admin/users/{tid}/access",
                                json={"roleType": role_type, "adminId": admin_id},
                            )
                            if rev.status_code != 200:
                                st.error(f"Could not revoke {role_type} role before deletion.")
                                revoke_failed = True
                                break
                    if not revoke_failed:
                        resp = api_request(
                            "DELETE",
                            f"{API}/admin/users/{tid}",
                            params={"adminId": admin_id},
                        )
                        if resp.status_code == 200:
                            st.success("User deleted.")
                            st.rerun()
                        else:
                            st.error(f"Delete failed: {resp.text}")
                elif access_resp.status_code == 404:
                    st.error("User not found.")
                else:
                    st.error(f"Could not check user roles: {access_resp.text}")
            except requests.exceptions.RequestException as e:
                api_error_banner(e)
