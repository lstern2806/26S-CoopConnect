"""System Settings — view, add, update, and delete platform settings (admin)."""

import logging

import requests
import streamlit as st

from modules.api import API_BASE_URL as API
from modules.api import api_error_banner, api_request, response_error_message
from modules.nav import PAGE_ICON, SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide", page_icon=PAGE_ICON)
SideBarLinks()
admin_id = st.session_state.get("admin_id", 1)

st.title("System Settings")

try:
    resp = api_request("GET", f"{API}/admin/system-settings")
    if resp.status_code == 200:
        st.dataframe(resp.json(), use_container_width=True)
    else:
        st.error(f"Could not load settings: {response_error_message(resp)}")
except requests.exceptions.RequestException as e:
    api_error_banner(e)

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
            add_resp = api_request("POST", f"{API}/admin/system-settings", json=payload)
            if add_resp.status_code == 201:
                st.success("Setting added.")
                st.rerun()
            else:
                st.error(f"Add failed: {response_error_message(add_resp)}")
        except requests.exceptions.RequestException as e:
            api_error_banner(e)

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
        upd_resp = api_request("PUT", f"{API}/admin/system-settings/{int(setting_id)}", json=payload)
        if upd_resp.status_code == 200:
            st.success("Setting updated.")
            st.rerun()
        else:
            st.error(f"Update failed: {response_error_message(upd_resp)}")
    except requests.exceptions.RequestException as e:
        api_error_banner(e)

if col2.button("Delete Setting"):
    try:
        del_resp = api_request("DELETE", f"{API}/admin/system-settings/{int(setting_id)}", params={"adminId": admin_id})
        if del_resp.status_code == 200:
            st.success("Setting deleted.")
            st.rerun()
        else:
            st.error(f"Delete failed: {response_error_message(del_resp)}")
    except requests.exceptions.RequestException as e:
        api_error_banner(e)
