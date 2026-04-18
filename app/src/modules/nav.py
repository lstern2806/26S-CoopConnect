# Idea borrowed from https://github.com/fsmosca/sample-streamlit-authenticator

# This file has functions to add links to the left sidebar based on the user's role.

import streamlit as st


# ---- General ----------------------------------------------------------------

def home_nav():
    st.sidebar.page_link("Home.py", label="Home", icon="🏠")


def about_page_nav():
    st.sidebar.page_link("pages/30_About.py", label="About", icon="🧠")


# ---- Role: student ----------------------------------------------------------

def student_home_nav():
    st.sidebar.page_link("pages/40_Student_Home.py", label="Student Home", icon="🎓")


def student_profile_nav():
    st.sidebar.page_link("pages/41_Student_Profile.py", label="My Profile", icon="👤")


def student_experiences_nav():
    st.sidebar.page_link("pages/42_Coop_Experiences.py", label="Co-op Experiences", icon="💼")


def student_outreach_nav():
    st.sidebar.page_link("pages/43_Student_Outreach.py", label="Student Outreach", icon="💬")


def employer_messages_nav():
    st.sidebar.page_link("pages/44_Employer_Messages.py", label="Employer Messages", icon="📩")


# ---- Role: advisor ----------------------------------------------------------

def advisor_home_nav():
    st.sidebar.page_link("pages/50_Advisor_Home.py", label="Advisor Home", icon="🧭")


def advisor_students_nav():
    st.sidebar.page_link("pages/51_Advisor_Students.py", label="Students", icon="👥")


def advisor_placements_nav():
    st.sidebar.page_link("pages/53_Advisor_Placements.py", label="Placements", icon="📊")


def advisor_networking_nav():
    st.sidebar.page_link("pages/54_Advisor_Networking.py", label="Networking", icon="🔗")


def advisor_reports_nav():
    st.sidebar.page_link("pages/55_Advisor_Reports.py", label="Reports", icon="📄")


# ---- Role: employer ---------------------------------------------------------

def employer_home_nav():
    st.sidebar.page_link("pages/60_Employer_Home.py", label="Employer Home", icon="🏢")


def employer_search_nav():
    st.sidebar.page_link("pages/61_Student_Search.py", label="Search Students", icon="🔎")


def employer_history_nav():
    st.sidebar.page_link("pages/63_Coop_History.py", label="Co-op History", icon="📚")

def employer_outreach_nav():
    st.sidebar.page_link("pages/62_Employer_Outreach.py", label="Send Outreach", icon = "✉️")

def employer_experience_reports_nav():
    st.sidebar.page_link("pages/64_Employer_Reports.py", label="Experience Reports", icon="🗒️")

def employer_stats_nav():
    st.sidebar.page_link("pages/65_Employer_Stats.py", label="Company Engagement", icon="📊")

def employer_role_admin_nav():
    st.sidebar.page_link("pages/66_Employer_Role_Admin.py", label="Role Admin", icon="👤")


# ---- Role: administrator ----------------------------------------------------

def admin_home_nav():
    st.sidebar.page_link("pages/70_Admin_Home.py", label="Admin Dashboard", icon="🖥️")


def admin_users_nav():
    st.sidebar.page_link("pages/71_User_Management.py", label="User Management", icon="👤")


def admin_access_nav():
    st.sidebar.page_link("pages/73_Role_Access.py", label="Role Access", icon="🔐")


def admin_settings_nav():
    st.sidebar.page_link("pages/74_System_Settings.py", label="System Settings", icon="⚙️")


def admin_audit_nav():
    st.sidebar.page_link("pages/75_Audit_Logs.py", label="Audit Logs", icon="🧾")


def admin_integrity_nav():
    st.sidebar.page_link("pages/76_Integrity_Check.py", label="Integrity Check", icon="✅")


# ---- Sidebar assembly -------------------------------------------------------

def SideBarLinks(show_home=False):
    """
    Renders sidebar navigation links based on the logged-in user's role.
    The role is stored in st.session_state when the user logs in on Home.py.
    """

    # Logo appears at the top of the sidebar on every page
    st.sidebar.image("assets/logo.png", width=150)

    # If no one is logged in, send them to the Home (login) page
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.switch_page("Home.py")

    if show_home:
        home_nav()

    if st.session_state["authenticated"]:

        if st.session_state["role"] == "student":
            student_home_nav()
            student_profile_nav()
            student_experiences_nav()
            student_outreach_nav()
            employer_messages_nav()

        if st.session_state["role"] == "advisor":
            advisor_home_nav()
            advisor_students_nav()
            advisor_placements_nav()
            advisor_networking_nav()
            advisor_reports_nav()

        if st.session_state["role"] == "employer":
            employer_home_nav()
            employer_search_nav()
            employer_history_nav()
            employer_outreach_nav()
            employer_experience_reports_nav()
            employer_stats_nav()
            employer_role_admin_nav()

        if st.session_state["role"] == "administrator":
            admin_home_nav()
            admin_users_nav()
            admin_access_nav()
            admin_settings_nav()
            admin_audit_nav()
            admin_integrity_nav()

    # About link appears at the bottom for all roles
    about_page_nav()

    if st.session_state["authenticated"]:
        if st.sidebar.button("Logout"):
            del st.session_state["role"]
            del st.session_state["authenticated"]
            st.switch_page("Home.py")
