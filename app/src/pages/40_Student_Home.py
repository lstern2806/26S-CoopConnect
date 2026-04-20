import logging

import streamlit as st

from modules.nav import PAGE_ICON, SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide", page_icon=PAGE_ICON)
SideBarLinks()

st.title("Student Home")
st.write(f"Welcome, {st.session_state.get('first_name', 'Student')}.")
st.write("Use the sidebar to manage your profile, experiences, and outreach.")
