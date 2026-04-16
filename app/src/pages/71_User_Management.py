import logging

import requests
import streamlit as st

from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
API = "http://localhost:4000"
admin_id = st.session_state.get("admin_id", 1)

st.title("User Management")

col1, col2 = st.columns(2)
status = col1.selectbox("Account status", ["", "active", "suspended"])
search = col2.text_input("Search by name or email")
params = {}
if status:
    params["status"] = status
if search:
    params["q"] = search

try:
    list_resp = requests.get(f"{API}/admin/users", params=params, timeout=10)
    if list_resp.status_code == 200:
        st.dataframe(list_resp.json(), use_container_width=True)
    else:
        st.error(f"Could not load users: {list_resp.text}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running on http://localhost:4000")

st.subheader("Create User")
with st.form("create_user"):
    first = st.text_input("First name")
    last = st.text_input("Last name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    account_status = st.selectbox("Status", ["active", "suspended"])
    create_submit = st.form_submit_button("Create User", type="primary")
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
            resp = requests.post(f"{API}/admin/users", json=payload, timeout=10)
            if resp.status_code == 201:
                st.success("User created.")
                st.rerun()
            else:
                st.error(f"Create failed: {resp.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to the API: {str(e)}")
            st.info("Please ensure the API server is running on http://localhost:4000")

st.subheader("Update or Delete User")
target_id = st.number_input("Target User ID", min_value=1, step=1)
new_first = st.text_input("New first name (optional)")
new_last = st.text_input("New last name (optional)")
new_email = st.text_input("New email (optional)")
new_status = st.selectbox("New status (optional)", ["", "active", "suspended"])
colu1, colu2 = st.columns(2)
if colu1.button("Update User"):
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
        resp = requests.put(f"{API}/admin/users/{int(target_id)}", json=payload, timeout=10)
        if resp.status_code == 200:
            st.success("User updated.")
            st.rerun()
        else:
            st.error(f"Update failed: {resp.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the API: {str(e)}")
        st.info("Please ensure the API server is running on http://localhost:4000")

if colu2.button("Delete User"):
    try:
        resp = requests.delete(f"{API}/admin/users/{int(target_id)}", params={"adminId": admin_id}, timeout=10)
        if resp.status_code == 200:
            st.success("User deleted.")
            st.rerun()
        else:
            st.error(f"Delete failed: {resp.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the API: {str(e)}")
        st.info("Please ensure the API server is running on http://localhost:4000")
