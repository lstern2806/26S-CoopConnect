import streamlit as st
from modules.nav import PAGE_ICON, SideBarLinks

st.set_page_config(layout='wide', page_icon=PAGE_ICON)

SideBarLinks()

st.write("# About this App")

st.markdown(
    """
    This is a demo app for CoopConnect.  

    The goal of this demo is to provide information on the tech stack 
    being used as well as demo some of the features of the various platforms. 

    Stay tuned for more information and features to come!
    """
)

# Add a button to return to home page
if st.button("Return to Home", type="primary"):
    st.switch_page("Home.py")
