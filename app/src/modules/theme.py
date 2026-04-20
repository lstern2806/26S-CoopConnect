"""
Shared theming for the CoopConnect Streamlit app.

Centralizes the black / red / white networking-app aesthetic so every page
has a consistent look. Call `apply_theme()` once near the top of each page
(after `st.set_page_config` and `SideBarLinks()`).

Helpers:
    apply_theme()                -> injects the global CSS
    page_hero(title, subtitle)   -> red gradient hero banner
    avatar_initials(name)        -> 2-letter initials for avatar circles
    avatar_color(seed)           -> deterministic accent color from a string
"""

import hashlib
import streamlit as st


# Palette ---------------------------------------------------------------------
COLORS = {
    "red":        "#C8102E",
    "red_dark":   "#8B0000",
    "red_soft":   "#FDECEC",
    "black":      "#0E0E0E",
    "ink":        "#1A1A1A",
    "muted":      "#6B6B6B",
    "line":       "#ECECEC",
    "bg":         "#FAFAFA",
    "white":      "#FFFFFF",
    "green":      "#1E8A4D",
    "amber":      "#E0A800",
}


_GLOBAL_CSS = f"""
<style>
/* ---------- App background + typography ---------- */
.stApp {{
    background: {COLORS["bg"]};
}}
html, body, [class*="css"] {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                 Roboto, "Helvetica Neue", Arial, sans-serif;
    color: {COLORS["ink"]};
}}

/* ---------- Hero banner ---------- */
.cc-hero {{
    background: linear-gradient(135deg, {COLORS["black"]} 0%, {COLORS["red_dark"]} 55%, {COLORS["red"]} 100%);
    color: {COLORS["white"]};
    padding: 1.75rem 2rem;
    border-radius: 18px;
    margin-bottom: 1.4rem;
    box-shadow: 0 8px 22px rgba(200,16,46,0.18);
}}
.cc-hero h1 {{
    color: {COLORS["white"]} !important;
    margin: 0;
    font-size: 1.9rem;
    font-weight: 700;
    letter-spacing: -0.01em;
}}
.cc-hero p {{
    color: #ffd9d9;
    margin: .35rem 0 0 0;
    font-size: .95rem;
}}

/* ---------- Section header with red accent ---------- */
.cc-section {{
    display: flex; align-items: center; gap: .6rem;
    margin: 1.2rem 0 .6rem 0;
}}
.cc-section .bar {{
    width: 4px; height: 22px; border-radius: 3px;
    background: {COLORS["red"]};
}}
.cc-section h3 {{
    margin: 0; font-size: 1.15rem; color: {COLORS["black"]};
    font-weight: 700;
}}

/* ---------- KPI cards ---------- */
.cc-kpi {{
    background: {COLORS["white"]};
    border: 1px solid {COLORS["line"]};
    border-radius: 14px;
    padding: 1.1rem 1.2rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: transform .15s ease, box-shadow .15s ease;
    animation: cc-fade .35s ease;
}}
.cc-kpi:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 18px rgba(0,0,0,0.08);
}}
.cc-kpi .label {{
    font-size: .78rem; color: {COLORS["muted"]};
    text-transform: uppercase; letter-spacing: .06em; margin: 0;
}}
.cc-kpi .value {{
    font-size: 2rem; font-weight: 800; color: {COLORS["black"]};
    margin: .35rem 0 .15rem 0; line-height: 1;
}}
.cc-kpi .delta {{
    color: {COLORS["green"]}; font-size: .8rem; font-weight: 600;
}}
.cc-kpi .delta.red {{ color: {COLORS["red"]}; }}

/* ---------- Pill / badge ---------- */
.cc-pill {{
    display: inline-block; padding: .2rem .65rem; border-radius: 999px;
    background: {COLORS["red_soft"]}; color: {COLORS["red"]};
    font-weight: 600; font-size: .78rem;
}}
.cc-pill.black {{
    background: {COLORS["black"]}; color: {COLORS["white"]};
}}
.cc-pill.light {{
    background: #F1F1F1; color: {COLORS["ink"]};
}}

/* ---------- Avatar circle ---------- */
.cc-avatar {{
    display: inline-flex; align-items: center; justify-content: center;
    width: 44px; height: 44px; border-radius: 50%;
    color: {COLORS["white"]}; font-weight: 700; font-size: .95rem;
    flex-shrink: 0;
}}

/* ---------- Student / person card ---------- */
.cc-person {{
    display: flex; gap: .9rem; align-items: center;
    background: {COLORS["white"]};
    border: 1px solid {COLORS["line"]};
    border-radius: 14px;
    padding: .9rem 1rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    transition: all .15s ease;
    animation: cc-fade .35s ease;
}}
.cc-person:hover {{
    border-color: {COLORS["red"]};
    transform: translateX(3px);
    box-shadow: 0 6px 14px rgba(200,16,46,0.08);
}}
.cc-person .body {{ flex: 1; min-width: 0; }}
.cc-person .name {{
    font-weight: 700; color: {COLORS["black"]};
    font-size: 1rem; margin: 0;
}}
.cc-person .meta {{
    color: {COLORS["muted"]}; font-size: .82rem; margin: .15rem 0 0 0;
}}
.cc-person .right {{
    display: flex; flex-direction: column; align-items: flex-end; gap: .3rem;
}}

/* ---------- Message / inbox row ---------- */
.cc-msg {{
    display: flex; gap: .9rem; align-items: flex-start;
    background: {COLORS["white"]};
    border: 1px solid {COLORS["line"]};
    border-left: 4px solid {COLORS["red"]};
    border-radius: 12px;
    padding: .85rem 1rem;
    margin-bottom: .6rem;
    animation: cc-fade .35s ease;
    transition: background .15s ease;
}}
.cc-msg:hover {{ background: #FFFBFB; }}
.cc-msg.muted {{ border-left-color: {COLORS["line"]}; }}
.cc-msg .body {{ flex: 1; min-width: 0; }}
.cc-msg .head {{
    display: flex; justify-content: space-between; gap: .5rem;
    align-items: baseline;
}}
.cc-msg .from {{ font-weight: 700; color: {COLORS["black"]}; }}
.cc-msg .time {{ color: {COLORS["muted"]}; font-size: .78rem; }}
.cc-msg .preview {{
    color: {COLORS["ink"]}; font-size: .9rem;
    margin-top: .15rem;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}}
.cc-msg .stat-row {{
    display: flex; gap: .5rem; margin-top: .4rem;
}}

/* ---------- Placement / company card ---------- */
.cc-place {{
    background: {COLORS["white"]};
    border: 1px solid {COLORS["line"]};
    border-radius: 14px;
    padding: .9rem 1rem;
    margin-bottom: .6rem;
    display: flex; justify-content: space-between; align-items: center;
    animation: cc-fade .35s ease;
    transition: all .15s ease;
}}
.cc-place:hover {{ border-color: {COLORS["red"]}; }}
.cc-place .company {{ font-weight: 700; color: {COLORS["black"]}; font-size: 1rem; }}
.cc-place .industry {{ color: {COLORS["muted"]}; font-size: .82rem; margin-top: .15rem; }}

/* ---------- Report card ---------- */
.cc-report {{
    background: {COLORS["white"]};
    border: 1px solid {COLORS["line"]};
    border-radius: 14px;
    padding: 1rem 1.1rem;
    margin-bottom: .7rem;
    animation: cc-fade .35s ease;
    transition: all .15s ease;
}}
.cc-report:hover {{
    border-color: {COLORS["red"]};
    transform: translateY(-2px);
    box-shadow: 0 6px 14px rgba(0,0,0,0.05);
}}
.cc-report .title {{
    font-weight: 700; color: {COLORS["black"]}; font-size: 1.05rem;
}}
.cc-report .sub {{
    color: {COLORS["muted"]}; font-size: .82rem; margin-top: .2rem;
}}

/* ---------- Empty state ---------- */
.cc-empty {{
    text-align: center;
    padding: 2.5rem 1rem;
    border: 2px dashed {COLORS["line"]};
    border-radius: 14px;
    color: {COLORS["muted"]};
    background: {COLORS["white"]};
}}
.cc-empty .icon {{ font-size: 2.4rem; margin-bottom: .4rem; }}

/* ---------- Buttons (Streamlit overrides, light touch) ---------- */
.stButton > button[kind="primary"] {{
    background: {COLORS["red"]}; border-color: {COLORS["red"]};
}}
.stButton > button[kind="primary"]:hover {{
    background: {COLORS["red_dark"]}; border-color: {COLORS["red_dark"]};
}}

/* ---------- Tabs ---------- */
.stTabs [aria-selected="true"] {{
    color: {COLORS["red"]} !important;
}}
.stTabs [data-baseweb="tab-highlight"] {{
    background-color: {COLORS["red"]} !important;
}}

/* ---------- Keyframes ---------- */
@keyframes cc-fade {{
    from {{ opacity: 0; transform: translateY(4px); }}
    to   {{ opacity: 1; transform: translateY(0);   }}
}}
@keyframes cc-pulse {{
    0%, 100% {{ transform: scale(1); }}
    50%      {{ transform: scale(1.04); }}
}}
.cc-live-dot {{
    display: inline-block; width: 8px; height: 8px; border-radius: 50%;
    background: {COLORS["red"]}; margin-right: .35rem;
    animation: cc-pulse 1.6s ease infinite;
}}
</style>
"""


def apply_theme() -> None:
    """Inject the global CSS. Safe to call multiple times per page."""
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)


def page_hero(title: str, subtitle: str = "", emoji: str = "") -> None:
    """Render the red-gradient hero banner at the top of a page."""
    prefix = f"{emoji} " if emoji else ""
    st.markdown(
        f"""
        <div class="cc-hero">
            <h1>{prefix}{title}</h1>
            {f'<p>{subtitle}</p>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title: str) -> None:
    """Render a section heading with a red accent bar."""
    st.markdown(
        f"""
        <div class="cc-section">
            <div class="bar"></div><h3>{title}</h3>
        </div>
        """,
        unsafe_allow_html=True,
    )


def avatar_initials(name: str) -> str:
    parts = [p for p in str(name).strip().split() if p]
    if not parts:
        return "??"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def avatar_color(seed: str) -> str:
    """Deterministic color from a seed string. Palette stays on-brand."""
    palette = [
        "#C8102E", "#0E0E0E", "#8B0000", "#3A3A3A",
        "#A10E25", "#5C0000", "#222222", "#7A0A20",
    ]
    h = int(hashlib.md5(str(seed).encode("utf-8")).hexdigest(), 16)
    return palette[h % len(palette)]


def avatar_html(name: str, size: int = 44) -> str:
    initials = avatar_initials(name)
    color = avatar_color(name)
    return (
        f'<div class="cc-avatar" '
        f'style="background:{color}; width:{size}px; height:{size}px; '
        f'font-size:{max(11, size//3)}px;">{initials}</div>'
    )


def empty_state(icon: str, title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="cc-empty">
            <div class="icon">{icon}</div>
            <div style="font-weight:700; color:#0E0E0E;">{title}</div>
            {f'<div style="margin-top:.25rem;">{subtitle}</div>' if subtitle else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )
