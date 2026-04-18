import logging
import os
import requests
import streamlit as st
import pandas as pd  # Added for data handling

from modules.nav import SideBarLinks

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide")
SideBarLinks()
API = os.getenv("API_BASE_URL", "http://localhost:4000")

st.title("Student Interest Analytics")
company_id = st.session_state.get("company_id")

if not company_id:
    st.error("Missing company_id in session. Please log in again from Home.")
    st.stop()

st.subheader("Trends in Student Interest Over Time")

try:
    # 1. Fetch data from your new analytics endpoint
    resp = requests.get(
        f"{API}/emp/analytics/interest_over_time", 
        params={"companyId": company_id}, 
        timeout=10
    )
    
    if resp.status_code == 200:
        data = resp.json()
        
        if data:
            # 2. Convert to DataFrame
            df = pd.DataFrame(data)
            
            # 3. Ensure 'day' is treated as a datetime object for proper sorting/spacing
            df['day'] = pd.to_datetime(df['day'])
            
            # 4. Display the line chart
            # We set 'day' as the x-axis and 'messageCount' as the y-axis
            st.line_chart(df, x="day", y="messageCount")
            
            # Optional: Show the raw data table below the chart
            with st.expander("View Raw Data"):
                st.dataframe(df, use_container_width=True)
        else:
            st.info("No interest data found for this company yet.")
            
    else:
        st.error(f"Could not load analytics: {resp.text}")

except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")


st.divider()


st.subheader("Comparison to other companies average")
company_id = st.session_state.get("company_id")

if not company_id:
    st.error("Missing company_id in session. Please log in again from Home.")
    st.stop()

# --- SECTION 1: PEER COMPARISON ---
st.subheader("Your Engagement vs. Peer Average")

try:
    comparison_resp = requests.get(
        f"{API}/emp/analytics/company_comparison", 
        params={"companyId": company_id}, 
        timeout=10
    )
    
    if comparison_resp.status_code == 200:
        comp_data = comparison_resp.json()
        
        if comp_data:
            df_comp = pd.DataFrame(comp_data)
            df_comp['day'] = pd.to_datetime(df_comp['day'])
            
            # Renaming columns for a cleaner legend in the UI
            df_comp = df_comp.rename(columns={
                "messageCount": "Your Company",
                "avgMessageOtherCompanies": "Companies Average"
            })
            
            # Setting the index to 'day' allows Streamlit to use it as the X-axis automatically
            df_comp.set_index("day", inplace=True)
            
            # Plotting both columns on one chart
            st.line_chart(df_comp)
        else:
            st.info("Not enough data to generate a peer comparison yet.")
    else:
        st.error(f"Could not load comparison: {comparison_resp.text}")

except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {str(e)}")