import logging

import streamlit as st

from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()

st.title("Employer Home")
st.write(f"Welcome, {st.session_state.get('first_name', 'Employer')}.")
st.write("Use the sidebar to search students and review co-op history.")
