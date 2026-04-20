"""
Advisor → Networking Inbox — outreach engagement in a chat/inbox layout.

Reads:
    GET /adv/networking-activity         — all advisees' engagement
    GET /adv/networking-activity/<id>    — drill-down for one student
"""

import logging
import os

import pandas as pd
import requests
import streamlit as st

from modules.nav import SideBarLinks
from modules.theme import (
    apply_theme, page_hero, section, avatar_html, empty_state, COLORS,
)

logger = logging.getLogger(__name__)

st.set_page_config(layout="wide", page_title="Networking Inbox · CoopConnect")
SideBarLinks()
apply_theme()

API = os.getenv("API_BASE_URL", "http://localhost:4000")

# ---- Hero ------------------------------------------------------------------
page_hero(
    title="Networking Inbox",
    subtitle="Who's reaching out, who's getting replies, who needs a nudge.",
    emoji="💬",
)

# ---- Fetch -----------------------------------------------------------------
activity = []
try:
    resp = requests.get(f"{API}/adv/networking-activity", timeout=10)
    if resp.status_code == 200:
        activity = resp.json() or []
    else:
        st.error(f"Could not load networking metrics: {resp.text}")
except requests.exceptions.RequestException as e:
    st.error(f"Error connecting to the API: {e}")
    st.info("Please ensure the API server is running on http://localhost:4000")

# ---- Toolbar: filter + sort ------------------------------------------------
with st.container(border=True):
    t1, t2, t3 = st.columns([2, 1.5, 1.5])
    q = t1.text_input("🔎 Search advisees", placeholder="Type a first or last name…")
    status_filter = t2.selectbox(
        "Filter",
        ["All", "🔥 Most active", "💤 Quiet (no outreach)", "✅ Has replies"],
        index=0,
    )
    sort_by = t3.selectbox(
        "Sort by",
        ["Most outreach", "Most replies", "Best response rate", "Name A–Z"],
        index=0,
    )

# ---- Derive metrics --------------------------------------------------------
def _rate(row):
    out = row.get("totalStudentOutreach", 0) or 0
    rep = row.get("totalEmployerResponses", 0) or 0
    return (rep / out) if out else 0.0

rows = []
for r in activity or []:
    rows.append({
        "studentId": r.get("studentId"),
        "name": f"{r.get('firstName','')} {r.get('lastName','')}".strip() or "Student",
        "outreach": r.get("totalStudentOutreach", 0) or 0,
        "replies": r.get("totalEmployerResponses", 0) or 0,
        "rate": _rate(r),
    })

# Apply search
if q:
    qq = q.lower().strip()
    rows = [r for r in rows if qq in r["name"].lower()]

# Apply status filter
if status_filter == "🔥 Most active":
    rows = [r for r in rows if r["outreach"] >= 3]
elif status_filter == "💤 Quiet (no outreach)":
    rows = [r for r in rows if r["outreach"] == 0]
elif status_filter == "✅ Has replies":
    rows = [r for r in rows if r["replies"] > 0]

# Apply sort
if sort_by == "Most outreach":
    rows.sort(key=lambda r: r["outreach"], reverse=True)
elif sort_by == "Most replies":
    rows.sort(key=lambda r: r["replies"], reverse=True)
elif sort_by == "Best response rate":
    rows.sort(key=lambda r: r["rate"], reverse=True)
else:
    rows.sort(key=lambda r: r["name"].lower())

# ---- KPI row ---------------------------------------------------------------
total_students = len(activity)
total_outreach = sum((r.get("totalStudentOutreach", 0) or 0) for r in activity)
total_replies  = sum((r.get("totalEmployerResponses", 0) or 0) for r in activity)
avg_rate = (total_replies / total_outreach) if total_outreach else 0.0
quiet_count = sum(1 for r in activity if (r.get("totalStudentOutreach", 0) or 0) == 0)

section("📊 Engagement pulse")
k1, k2, k3, k4 = st.columns(4)
for col, label, value, sub in [
    (k1, "👥 Students", total_students, "tracked"),
    (k2, "✉️ Outreach", total_outreach, "sent"),
    (k3, "💬 Replies",  total_replies,  "received"),
    (k4, "📈 Response rate", f"{avg_rate*100:.0f}%", "program avg"),
]:
    col.markdown(
        f"""
        <div class="cc-kpi">
            <p class="label">{label}</p>
            <p class="value">{value}</p>
            <p class="delta">● {sub}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

if quiet_count:
    st.toast(f"💤 {quiet_count} student{'s' if quiet_count != 1 else ''} "
             "haven't sent any outreach yet.", icon="🔔")

# ---- Inbox layout: list on left, preview on right --------------------------
st.write("")
section("📥 Inbox")

if not rows:
    empty_state(
        "📭", "No conversations match your filters",
        "Try clearing the search or switching the filter to 'All'.",
    )
else:
    left, right = st.columns([1.1, 1.2])

    with left:
        st.caption(f"{len(rows)} thread{'s' if len(rows) != 1 else ''}")
        # Selection via buttons so clicks update the preview
        if "selected_student_id" not in st.session_state:
            st.session_state["selected_student_id"] = rows[0]["studentId"]

        for r in rows:
            is_selected = r["studentId"] == st.session_state["selected_student_id"]
            border_color = COLORS["red"] if is_selected else COLORS["line"]
            bg = "#FFFBFB" if is_selected else COLORS["white"]

            status_pill = ""
            if r["outreach"] == 0:
                status_pill = '<span class="cc-pill">💤 Quiet</span>'
            elif r["rate"] >= 0.5:
                status_pill = '<span class="cc-pill black">🔥 Hot thread</span>'
            elif r["replies"] > 0:
                status_pill = '<span class="cc-pill">✅ Replied</span>'

            preview_text = (
                f"✉️ {r['outreach']} outreach · 💬 {r['replies']} replies"
                if r["outreach"] or r["replies"] else
                "No activity yet — send them a nudge"
            )

            st.markdown(
                f"""
                <div class="cc-msg" style="border-color:{border_color}; background:{bg};
                                           border-left-color:{COLORS['red'] if is_selected else COLORS['line']};">
                    {avatar_html(r['name'], size=42)}
                    <div class="body">
                        <div class="head">
                            <span class="from">{r['name']}</span>
                            <span class="time">#{r['studentId']}</span>
                        </div>
                        <div class="preview">{preview_text}</div>
                        <div class="stat-row">{status_pill}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Open thread · {r['name']}", key=f"pick_{r['studentId']}",
                         use_container_width=True):
                st.session_state["selected_student_id"] = r["studentId"]
                st.rerun()

    with right:
        sel_id = st.session_state.get("selected_student_id")
        sel_row = next((r for r in rows if r["studentId"] == sel_id), rows[0])

        st.markdown(
            f"""
            <div class="cc-hero" style="padding:1.2rem 1.4rem; border-radius:14px;
                                        margin-bottom:1rem;">
                <div style="display:flex; align-items:center; gap:.9rem;">
                    {avatar_html(sel_row['name'], size=52)}
                    <div>
                        <div style="font-weight:700; font-size:1.2rem;">{sel_row['name']}</div>
                        <div style="color:#ffd9d9; font-size:.85rem;">
                            Student #{sel_row['studentId']} · Engagement detail
                        </div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Per-student metric cards
        mc1, mc2, mc3 = st.columns(3)
        for col, label, val in [
            (mc1, "✉️ Outreach sent", sel_row["outreach"]),
            (mc2, "💬 Replies",       sel_row["replies"]),
            (mc3, "📈 Response rate", f"{sel_row['rate']*100:.0f}%"),
        ]:
            col.markdown(
                f"""
                <div class="cc-kpi">
                    <p class="label">{label}</p>
                    <p class="value" style="font-size:1.5rem;">{val}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Simulated message thread (based on real counts)
        st.write("")
        st.markdown("##### 💬 Thread preview")
        st.caption("Generated from live outreach counts from the database.")

        if sel_row["outreach"] == 0:
            st.info("This student hasn't sent any outreach yet. "
                    "Consider opening a check-in.")
        else:
            # Show a few stylized bubbles representing the activity
            st.markdown(
                f"""
                <div class="cc-msg">
                    {avatar_html(sel_row['name'], size=36)}
                    <div class="body">
                        <div class="head">
                            <span class="from">{sel_row['name']}</span>
                            <span class="time">sent outreach</span>
                        </div>
                        <div class="preview">
                            Reached out to {sel_row['outreach']} employer{'s' if sel_row['outreach']!=1 else ''}.
                        </div>
                    </div>
                </div>
                <div class="cc-msg muted">
                    <div class="cc-avatar" style="background:{COLORS['black']}; width:36px; height:36px; font-size:12px;">CO</div>
                    <div class="body">
                        <div class="head">
                            <span class="from">Employers</span>
                            <span class="time">replied</span>
                        </div>
                        <div class="preview">
                            {sel_row['replies']} repl{'y' if sel_row['replies']==1 else 'ies'}
                            received so far.
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Mini trend view for this student if there's activity
        if sel_row["outreach"] or sel_row["replies"]:
            st.write("")
            df = pd.DataFrame({
                "metric":  ["Outreach", "Replies"],
                "count":   [sel_row["outreach"], sel_row["replies"]],
            }).set_index("metric")
            st.bar_chart(df, height=200, color=COLORS["red"])
