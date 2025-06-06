import streamlit as st
import requests
import time
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="Live Sports Scores", layout="wide")

# Animation CSS
st.markdown("""
    <style>
    @keyframes fadeIn {
        0% {opacity: 0;}
        100% {opacity: 1;}
    }
    .fade-in {
        animation: fadeIn 0.8s ease-in;
    }
    .blinking {
        animation: blinker 1s linear infinite;
    }
    @keyframes blinker {
        50% { opacity: 0.5; }
    }
    .refresh-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(255, 255, 255, 0.8);
        z-index: 9999;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 2em;
        font-weight: bold;
        animation: fadeIn 0.5s ease-in;
    }
    </style>
""", unsafe_allow_html=True)

# Session state init
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False
if "schedule_cache" not in st.session_state:
    st.session_state.schedule_cache = {}
if "cache_timestamps" not in st.session_state:
    st.session_state.cache_timestamps = {}
if "show_refresh_overlay" not in st.session_state:
    st.session_state.show_refresh_overlay = False

# Sidebar controls
col1, col2 = st.sidebar.columns(2)
if col1.button("🔁 Refresh Now"):
    st.session_state.last_refresh = time.time()
    st.session_state.show_refresh_overlay = True
    for league_cfg in [v for v in SPORTS.values()]:
        _ = get_scores(league_cfg["path"])
    st.rerun()

if col2.button("⏯ Toggle Auto-Refresh"):
    st.session_state.auto_refresh = not st.session_state.auto_refresh

# Refresh logic
now = time.time()
auto_refresh_interval = 5
should_refresh = st.session_state.auto_refresh and (now - st.session_state.last_refresh > auto_refresh_interval)

if should_refresh:
    st.session_state.last_refresh = now
    st.session_state.show_refresh_overlay = True
    for league_cfg in [v for v in SPORTS.values()]:
        _ = get_scores(league_cfg["path"])
    st.rerun()

# Invalidate expired cache keys
expired_keys = [
    k for k, ts in st.session_state.cache_timestamps.items()
    if now - ts > 5
]
for k in expired_keys:
    st.session_state.schedule_cache.pop(k, None)
    st.session_state.cache_timestamps.pop(k, None)

if st.session_state.get("show_refresh_overlay"):
    st.markdown("<div class='refresh-overlay'>Refreshing...</div>", unsafe_allow_html=True)
    st.session_state.show_refresh_overlay = False

SPORTS = {
    "NFL (Football)": {"path": "football/nfl", "icon": "🏈"},
    "NBA (Basketball)": {"path": "basketball/nba", "icon": "🏀"},
    "MLB (Baseball)": {"path": "baseball/mlb", "icon": "⚾"},
    "NHL (Hockey)": {"path": "hockey/nhl", "icon": "🏒"}
}

TEAM_COLORS = {
    "NE": "#002244", "DAL": "#003594", "GB": "#203731", "KC": "#E31837", "PHI": "#004C54",
    "SF": "#AA0000", "CHI": "#0B162A", "PIT": "#FFB612",
    "LAL": "#552583", "BOS": "#007A33", "GSW": "#1D428A", "MIA": "#98002E", "NYK": "#F58426",
    "NYY": "#003087", "LAD": "#005A9C", "CHC": "#0E3386", "HOU": "#EB6E1F",
    "NYR": "#0038A8", "TOR": "#00205B", "VGK": "#B4975A"
}

# The rest of the code remains unchanged, including get_scores and display_scores definitions.
# UI rendering:
st.title("📻 Live Sports Scores Dashboard")
st.markdown("Real-time updates with team logos and stats.")

date_selection = st.sidebar.date_input("Select date (for past games):", datetime.today())
selected_sport = st.sidebar.selectbox("Select a sport:", list(SPORTS.keys()))
formatted_date = date_selection.strftime("%Y%m%d")
display_scores(selected_sport, formatted_date)
