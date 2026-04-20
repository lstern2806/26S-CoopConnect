"""Role Access — structured account view and editing (Streamlit admin)."""

import logging
import os

import requests
import streamlit as st

from modules.nav import PAGE_ICON, SideBarLinks

logger = logging.getLogger(__name__)


def api_request(method: str, url: str, **kwargs):
    """Perform HTTP request with consistent timeout; return response or raise."""
    return requests.request(method, url, timeout=10, **kwargs)


def api_error_banner(exc: requests.exceptions.RequestException):
    st.error(f"Error connecting to the API: {exc}")
    st.caption("Ensure the API server is running (default: http://localhost:4000).")


def current_assignable_role(access_data: dict):
    """Single ADVISOR/STUDENT/EMPLOYER row from access payload (priority: advisor, student, employer)."""
    if not access_data:
        return None
    if access_data.get("advisor"):
        return "ADVISOR"
    if access_data.get("student"):
        return "STUDENT"
    if access_data.get("employer"):
        return "EMPLOYER"
    return None


def default_assign_payload(role_type: str, admin_id: int) -> dict:
    """Minimal POST body for POST /admin/users/{id}/access after a role swap."""
    payload = {"roleType": role_type, "adminId": admin_id}
    if role_type == "ADVISOR":
        payload["department"] = ""
    elif role_type == "STUDENT":
        payload.update({"major": "Undeclared", "GPA": 0.0, "gradYear": 2027})
    else:
        payload.update({"companyId": 1, "jobTitle": ""})
    return payload


API = os.getenv("API_BASE_URL", "http://localhost:4000")

st.set_page_config(layout="wide", page_icon=PAGE_ICON)
SideBarLinks()

if "prefill_role_access_user_id" in st.session_state:
    st.session_state["_role_access_loaded_uid"] = int(
        st.session_state.pop("prefill_role_access_user_id")
    )
    st.session_state["_role_access_autoload"] = True

admin_id = st.session_state.get("admin_id", 1)

st.title("Role Access")
st.caption(
    "Select an account by User ID, load details, then edit profile or role access as needed."
)

if "_role_access_loaded_uid" not in st.session_state:
    st.session_state["_role_access_loaded_uid"] = 1

if st.session_state.pop("_role_access_autoload", False):
    _auid = int(st.session_state["_role_access_loaded_uid"])
    try:
        _ur = api_request("GET", f"{API}/admin/users/{_auid}")
        _ar = api_request("GET", f"{API}/admin/users/{_auid}/access")
        if _ur.status_code == 200 and _ar.status_code == 200:
            st.session_state["_role_access_user_payload"] = _ur.json()
            st.session_state["_role_access_access_payload"] = _ar.json()
        elif _ur.status_code != 200:
            st.error(f"Could not load user {_auid}: {_ur.text}")
        else:
            st.error(f"Could not load access for {_auid}: {_ar.text}")
    except requests.exceptions.RequestException as e:
        api_error_banner(e)

col_sel, col_btn = st.columns([2, 1])
with col_sel:
    user_id_val = st.number_input(
        "User ID",
        min_value=1,
        step=1,
        value=st.session_state["_role_access_loaded_uid"],
        key="role_access_uid_input",
    )
with col_btn:
    load_clicked = st.button("Load Access Details", type="primary")

if load_clicked:
    st.session_state["_role_access_loaded_uid"] = int(user_id_val)

uid = int(st.session_state["_role_access_loaded_uid"])

user_row = None
access_row = None

if load_clicked:
    try:
        u_resp = api_request("GET", f"{API}/admin/users/{uid}")
        a_resp = api_request("GET", f"{API}/admin/users/{uid}/access")
        if u_resp.status_code != 200:
            st.error(f"Could not load user: {u_resp.text}")
        elif a_resp.status_code != 200:
            st.error(f"Could not load access: {a_resp.text}")
        else:
            st.session_state["_role_access_user_payload"] = u_resp.json()
            st.session_state["_role_access_access_payload"] = a_resp.json()
            st.success("Loaded account details.")
            st.rerun()
    except requests.exceptions.RequestException as e:
        api_error_banner(e)

user_row = st.session_state.get("_role_access_user_payload")
access_row = st.session_state.get("_role_access_access_payload")

shown_uid = int(user_row["userId"]) if user_row and user_row.get("userId") else None
if shown_uid is not None and shown_uid != int(user_id_val):
    st.warning(
        f"Showing loaded user **{shown_uid}**. Change the User ID above and click **Load Access Details** to switch."
    )

if user_row and access_row:
    st.divider()

    with st.container(border=True):
        st.subheader("Account profile")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("User ID", user_row.get("userId", "—"))
        c2.metric("Name", f"{user_row.get('firstName', '')} {user_row.get('lastName', '')}".strip())
        c3.metric("Email", user_row.get("email", "—") or "—")
        c4.metric("Status", user_row.get("accountStatus", "—") or "—")
        if user_row.get("roles"):
            st.caption(f"**Role tags:** {user_row['roles']}")
        else:
            st.caption("**Role tags:** (none)")

    with st.expander("Edit account profile", expanded=False):
        _role_opts = ["STUDENT", "ADVISOR", "EMPLOYER"]
        _cur_assign = current_assignable_role(access_row)
        _default_role_idx = (
            _role_opts.index(_cur_assign) if _cur_assign in _role_opts else 0
        )
        with st.form("edit_user_profile"):
            ef = st.text_input("First name", value=user_row.get("firstName") or "")
            el = st.text_input("Last name", value=user_row.get("lastName") or "")
            ee = st.text_input("Email", value=user_row.get("email") or "")
            er = st.selectbox(
                "Role Assigned",
                _role_opts,
                index=_default_role_idx,
                key=f"edit_profile_role_assigned_{uid}",
                help="Changing role revokes the previous STUDENT/ADVISOR/EMPLOYER assignment and assigns the selected one with placeholder fields you can edit below.",
            )
            es = st.selectbox(
                "Account status",
                ["active", "suspended"],
                index=0 if (user_row.get("accountStatus") or "active") == "active" else 1,
            )
            up_submit = st.form_submit_button("Save profile changes")
            if up_submit:
                payload = {"adminId": admin_id}
                if ef:
                    payload["firstName"] = ef
                if el:
                    payload["lastName"] = el
                if ee:
                    payload["email"] = ee
                payload["accountStatus"] = es
                try:
                    r = api_request(
                        "PUT",
                        f"{API}/admin/users/{uid}",
                        json=payload,
                    )
                    if r.status_code != 200:
                        st.error(f"Update failed: {r.text}")
                    else:
                        st.success("Profile updated.")
                        old_assign = current_assignable_role(access_row)
                        role_changed = er != old_assign
                        if role_changed:
                            if old_assign:
                                dr = api_request(
                                    "DELETE",
                                    f"{API}/admin/users/{uid}/access",
                                    params={
                                        "roleType": old_assign,
                                        "adminId": admin_id,
                                    },
                                )
                                if dr.status_code != 200:
                                    st.error(
                                        f"Could not revoke previous role ({old_assign}): {dr.text}"
                                    )
                                else:
                                    pr = api_request(
                                        "POST",
                                        f"{API}/admin/users/{uid}/access",
                                        json=default_assign_payload(er, admin_id),
                                    )
                                    if pr.status_code not in [200, 201]:
                                        st.warning(
                                            f"Profile saved but role assignment failed: {pr.text}"
                                        )
                                    else:
                                        st.success(
                                            f"Role changed to **{er}**. Adjust details under **Edit existing role fields** if needed."
                                        )
                            else:
                                pr = api_request(
                                    "POST",
                                    f"{API}/admin/users/{uid}/access",
                                    json=default_assign_payload(er, admin_id),
                                )
                                if pr.status_code not in [200, 201]:
                                    st.warning(
                                        f"Profile saved but role assignment failed: {pr.text}"
                                    )
                                else:
                                    st.success(
                                        f"Assigned role **{er}**. Adjust details under **Edit existing role fields** if needed."
                                    )
                        ur = api_request("GET", f"{API}/admin/users/{uid}")
                        ar = api_request("GET", f"{API}/admin/users/{uid}/access")
                        if ur.status_code == 200:
                            st.session_state["_role_access_user_payload"] = ur.json()
                        if ar.status_code == 200:
                            st.session_state["_role_access_access_payload"] = ar.json()
                        st.rerun()
                except requests.exceptions.RequestException as e:
                    api_error_banner(e)

    st.divider()
    st.subheader("Role access")

    roles_meta = [
        ("admin", "Administrator", access_row.get("admin")),
        ("advisor", "Advisor", access_row.get("advisor")),
        ("student", "Student", access_row.get("student")),
        ("employer", "Employer", access_row.get("employer")),
    ]

    for _key, label, row in roles_meta:
        with st.container(border=True):
            st.markdown(f"##### {label}")
            if row is None:
                st.caption("_No role assigned._")
            else:
                ncols = min(4, max(1, len(row)))
                cols = st.columns(ncols)
                for i, (k, v) in enumerate(row.items()):
                    cols[i % ncols].markdown(f"**{k}**\n\n`{v}`")

    # Inline edit existing role (STUDENT / ADVISOR / EMPLOYER only — API limitation)
    existing_assignable = []
    if access_row.get("advisor"):
        existing_assignable.append("ADVISOR")
    if access_row.get("student"):
        existing_assignable.append("STUDENT")
    if access_row.get("employer"):
        existing_assignable.append("EMPLOYER")

    if existing_assignable:
        with st.expander("Edit existing role fields", expanded=False):
            edit_role = st.selectbox(
                "Role to update",
                existing_assignable,
                key="edit_existing_role_sel",
            )
            adv = access_row.get("advisor") or {}
            stu = access_row.get("student") or {}
            emp = access_row.get("employer") or {}

            if edit_role == "ADVISOR":
                dept_ed = st.text_input(
                    "Department",
                    value=str(adv.get("department") or ""),
                    key="adv_dept_ed",
                )
                if st.button("Save advisor fields", key="save_adv"):
                    try:
                        r = api_request(
                            "PUT",
                            f"{API}/admin/users/{uid}/access",
                            json={
                                "roleType": "ADVISOR",
                                "department": dept_ed,
                                "adminId": admin_id,
                            },
                        )
                        if r.status_code == 200:
                            st.success("Advisor role updated.")
                            ar = api_request("GET", f"{API}/admin/users/{uid}/access")
                            if ar.status_code == 200:
                                st.session_state["_role_access_access_payload"] = ar.json()
                            st.rerun()
                        else:
                            st.error(r.text)
                    except requests.exceptions.RequestException as e:
                        api_error_banner(e)

            elif edit_role == "STUDENT":
                c1, c2 = st.columns(2)
                adv_id_ed = c1.number_input(
                    "Advisor ID",
                    min_value=0,
                    step=1,
                    value=int(stu.get("advisorId") or 0),
                    key="stu_adv_ed",
                )
                maj_ed = c2.text_input("Major", value=str(stu.get("major") or ""), key="stu_maj_ed")
                gpa_ed = st.number_input(
                    "GPA",
                    min_value=0.0,
                    max_value=4.0,
                    value=float(stu.get("GPA") or 0.0),
                    step=0.1,
                    key="stu_gpa_ed",
                )
                gy_ed = st.number_input(
                    "Grad year",
                    min_value=1990,
                    max_value=2050,
                    value=int(stu.get("gradYear") or 2027),
                    step=1,
                    key="stu_gy_ed",
                )
                if st.button("Save student fields", key="save_stu"):
                    try:
                        payload = {
                            "roleType": "STUDENT",
                            "adminId": admin_id,
                            "major": maj_ed,
                            "GPA": gpa_ed,
                            "gradYear": int(gy_ed),
                        }
                        if int(adv_id_ed) > 0:
                            payload["advisorId"] = int(adv_id_ed)
                        r = api_request(
                            "PUT",
                            f"{API}/admin/users/{uid}/access",
                            json=payload,
                        )
                        if r.status_code == 200:
                            st.success("Student role updated.")
                            ar = api_request("GET", f"{API}/admin/users/{uid}/access")
                            if ar.status_code == 200:
                                st.session_state["_role_access_access_payload"] = ar.json()
                            st.rerun()
                        else:
                            st.error(r.text)
                    except requests.exceptions.RequestException as e:
                        api_error_banner(e)

            else:  # EMPLOYER
                c1, c2 = st.columns(2)
                cid_ed = c1.number_input(
                    "Company ID",
                    min_value=1,
                    step=1,
                    value=int(emp.get("companyId") or 1),
                    key="emp_cid_ed",
                )
                jt_ed = c2.text_input(
                    "Job title",
                    value=str(emp.get("jobTitle") or ""),
                    key="emp_jt_ed",
                )
                if st.button("Save employer fields", key="save_emp"):
                    try:
                        r = api_request(
                            "PUT",
                            f"{API}/admin/users/{uid}/access",
                            json={
                                "roleType": "EMPLOYER",
                                "companyId": int(cid_ed),
                                "jobTitle": jt_ed,
                                "adminId": admin_id,
                            },
                        )
                        if r.status_code == 200:
                            st.success("Employer role updated.")
                            ar = api_request("GET", f"{API}/admin/users/{uid}/access")
                            if ar.status_code == 200:
                                st.session_state["_role_access_access_payload"] = ar.json()
                            st.rerun()
                        else:
                            st.error(r.text)
                    except requests.exceptions.RequestException as e:
                        api_error_banner(e)

    st.divider()
    st.subheader("Assign or revoke role")
    role_type = st.selectbox(
        "Role type (assign / revoke)",
        ["STUDENT", "ADVISOR", "EMPLOYER"],
        key="assign_role_type",
    )

    if role_type == "ADVISOR":
        department = st.text_input("Advisor department", key="assign_dept")
    elif role_type == "STUDENT":
        advisor_id = st.number_input(
            "Advisor ID (0 if none)",
            min_value=0,
            step=1,
            key="assign_adv_id",
        )
        major = st.text_input("Major", key="assign_major")
        gpa = st.number_input(
            "GPA", min_value=0.0, max_value=4.0, value=3.0, step=0.1, key="assign_gpa"
        )
        grad_year = st.number_input(
            "Grad year", min_value=2025, max_value=2035, value=2027, step=1, key="assign_gy"
        )
    else:
        company_id = st.number_input("Company ID", min_value=1, step=1, key="assign_cid")
        job_title = st.text_input("Job title", key="assign_jt")

    ac1, ac2 = st.columns(2)
    if ac1.button("Assign role"):
        payload = {"roleType": role_type, "adminId": admin_id}
        if role_type == "ADVISOR":
            payload["department"] = department
        elif role_type == "STUDENT":
            payload.update({"major": major, "GPA": gpa, "gradYear": int(grad_year)})
            if int(advisor_id) > 0:
                payload["advisorId"] = int(advisor_id)
        else:
            payload.update({"companyId": int(company_id), "jobTitle": job_title})
        try:
            resp = api_request(
                "POST",
                f"{API}/admin/users/{uid}/access",
                json=payload,
            )
            if resp.status_code in [200, 201]:
                st.success("Role assigned.")
                ur = api_request("GET", f"{API}/admin/users/{uid}")
                ar = api_request("GET", f"{API}/admin/users/{uid}/access")
                if ur.status_code == 200:
                    st.session_state["_role_access_user_payload"] = ur.json()
                if ar.status_code == 200:
                    st.session_state["_role_access_access_payload"] = ar.json()
                st.rerun()
            else:
                try:
                    err_msg = resp.json().get("error", resp.text)
                except Exception:
                    err_msg = resp.text
                st.error(f"Error: {err_msg}")
        except requests.exceptions.RequestException as e:
            api_error_banner(e)

    if ac2.button("Revoke role"):
        try:
            resp = api_request(
                "DELETE",
                f"{API}/admin/users/{uid}/access",
                params={"roleType": role_type, "adminId": admin_id},
            )
            if resp.status_code == 200:
                st.success("Role removed.")
                ur = api_request("GET", f"{API}/admin/users/{uid}")
                ar = api_request("GET", f"{API}/admin/users/{uid}/access")
                if ur.status_code == 200:
                    st.session_state["_role_access_user_payload"] = ur.json()
                if ar.status_code == 200:
                    st.session_state["_role_access_access_payload"] = ar.json()
                st.rerun()
            else:
                st.error(f"Revoke failed: {resp.text}")
        except requests.exceptions.RequestException as e:
            api_error_banner(e)

else:
    st.info('Enter a User ID and click **Load Access Details** to view and edit an account.')
