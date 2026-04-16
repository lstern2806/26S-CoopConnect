import logging
import os

import requests
import streamlit as st

from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
API = os.getenv("API_BASE_URL", "http://localhost:4000")
admin_id = st.session_state.get("admin_id", 1)

st.title("System Settings")

try:
    resp = requests.get(f"{API}/admin/system-settings", timeout=10)
    if resp.status_code == 200:
        st.dataframe(resp.json(), use_container_width=True)
    else:
        st.error(f"Could not load settings: {resp.text}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")
    st.info("Please ensure the API server is running on http://localhost:4000")

with st.form("add_setting"):
    name = st.text_input("Setting name")
    value = st.text_input("Setting value")
    description = st.text_area("Description")
    submit = st.form_submit_button("Add Setting", type="primary")
    if submit:
        payload = {
            "updatedBy": admin_id,
            "settingName": name,
            "settingValue": value,
            "settingDescription": description,
        }
        try:
            add_resp = requests.post(f"{API}/admin/system-settings", json=payload, timeout=10)
            if add_resp.status_code == 201:
                st.success("Setting added.")
                st.rerun()
            else:
                st.error(f"Add failed: {add_resp.text}")
        except requests.exceptions.RequestException as e:
            st.error(f"Error connecting to the API: {str(e)}")
            st.info("Please ensure the API server is running on http://localhost:4000")

setting_id = st.number_input("Setting ID", min_value=1, step=1)
new_value = st.text_input("New value")
new_desc = st.text_input("New description")
col1, col2 = st.columns(2)
if col1.button("Update Setting"):
    payload = {"updatedBy": admin_id}
    if new_value:
        payload["settingValue"] = new_value
    if new_desc:
        payload["settingDescription"] = new_desc
    try:
        upd_resp = requests.put(f"{API}/admin/system-settings/{int(setting_id)}", json=payload, timeout=10)
        if upd_resp.status_code == 200:
            st.success("Setting updated.")
            st.rerun()
        else:
            st.error(f"Update failed: {upd_resp.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the API: {str(e)}")
        st.info("Please ensure the API server is running on http://localhost:4000")

if col2.button("Delete Setting"):
    try:
        del_resp = requests.delete(f"{API}/admin/system-settings/{int(setting_id)}", params={"adminId": admin_id}, timeout=10)
        if del_resp.status_code == 200:
            st.success("Setting deleted.")
            st.rerun()
        else:
            st.error(f"Delete failed: {del_resp.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the API: {str(e)}")
        st.info("Please ensure the API server is running on http://localhost:4000")
