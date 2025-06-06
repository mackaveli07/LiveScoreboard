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
if "selected_sport" not in st.session_state:
    st.session_state.selected_sport = list(SPORTS.keys())[0]

# Helper function
score_cache = {}

def get_scores(sport_path, date=None):
    cache_key = f"{sport_path}-{date or 'live'}"
    now = time.time()
    if cache_key in st.session_state.schedule_cache:
        return st.session_state.schedule_cache[cache_key]

    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard"
    if date:
        url += f"?dates={date}"
    try:
        response = requests.get(url)
        data = response.json()
    except Exception as e:
        st.error(f"Error fetching scores: {e}")
        return []

    results = []
    for event in data.get("events", []):
        comp = event['competitions'][0]
        teams = comp['competitors']
        if len(teams) != 2:
            continue
        t1, t2 = teams

        possession = comp.get("situation", {}).get("possession")
        results.append({
            "id": event['id'],
            "status": comp['status']['type']['shortDetail'],
            "teams": [
                {
                    "name": t1['team']['displayName'],
                    "score": t1['score'],
                    "logo": t1['team']['logo'],
                    "abbreviation": t1['team']['abbreviation'],
                    "possession": t1['team']['id'] == possession
                },
                {
                    "name": t2['team']['displayName'],
                    "score": t2['score'],
                    "logo": t2['team']['logo'],
                    "abbreviation": t2['team']['abbreviation'],
                    "possession": t2['team']['id'] == possession
                }
            ],
            "period": comp['status'].get("period", ""),
            "clock": comp['status'].get("displayClock", "")
        })

    st.session_state.schedule_cache[cache_key] = results
    st.session_state.cache_timestamps[cache_key] = now
    return results

def display_scores(sport_name, date):
    sport_cfg = SPORTS[sport_name]
    scores = get_scores(sport_cfg['path'], date)
    if not scores:
        st.info("No games available.")
        return

    for game in scores:
        t1, t2 = game['teams']
        game_id = game['id']
        prev = score_cache.get(game_id, (None, None))
        score_cache[game_id] = (t1['score'], t2['score'])
        b1 = " blinking" if prev[0] != t1['score'] and prev[0] is not None else ""
        b2 = " blinking" if prev[1] != t2['score'] and prev[1] is not None else ""

        col1, col2, col3 = st.columns([4, 2, 4])
        with col1:
            st.image(t1['logo'], width=60)
            st.markdown(f"### {t1['name']}")
            st.markdown(f"<div class='fade-in{b1}'><strong>{t1['score']}</strong></div>", unsafe_allow_html=True)
            if t1['possession']:
                st.markdown("🏈 Possession")

        with col2:
            st.markdown(f"### VS")
            st.markdown(f"**{game['status']}**")
            st.markdown(f"Period: {game['period']}")
            st.markdown(f"Clock: {game['clock']}")

        with col3:
            st.image(t2['logo'], width=60)
            st.markdown(f"### {t2['name']}")
            st.markdown(f"<div class='fade-in{b2}'><strong>{t2['score']}</strong></div>", unsafe_allow_html=True)
            if t2['possession']:
                st.markdown("🏈 Possession")

        st.markdown("---")

# Sidebar controls
col1, col2 = st.sidebar.columns(2)
if col1.button("🔁 Refresh Now"):
    st.session_state.last_refresh = time.time()
    st.session_state.show_refresh_overlay = True
    sport_cfg = SPORTS[st.session_state.selected_sport]
    _ = get_scores(sport_cfg["path"])
    st.rerun()

if col2.button("⏯ Toggle Auto-Refresh"):
    st.session_state.auto_refresh = not st.session_state.auto_refresh

# Main content
st.title("📻 Live Sports Scores Dashboard")
st.markdown("Real-time updates with team logos and stats.")

date_selection = st.sidebar.date_input("Select date (for past games):", datetime.today())
selected_sport = st.sidebar.selectbox("Select a sport:", list(SPORTS.keys()))
st.session_state.selected_sport = selected_sport
formatted_date = date_selection.strftime("%Y%m%d")

# Refresh logic
now = time.time()
auto_refresh_interval = 5
should_refresh = st.session_state.auto_refresh and (now - st.session_state.last_refresh > auto_refresh_interval)
if should_refresh:
    st.session_state.last_refresh = now
    st.session_state.show_refresh_overlay = True
    sport_cfg = SPORTS[st.session_state.selected_sport]
    _ = get_scores(sport_cfg["path"])
    st.rerun()

# Invalidate expired cache
expired = [k for k, ts in st.session_state.cache_timestamps.items() if now - ts > 5]
for k in expired:
    st.session_state.schedule_cache.pop(k, None)
    st.session_state.cache_timestamps.pop(k, None)

if st.session_state.get("show_refresh_overlay"):
    st.markdown("<div class='refresh-overlay'>Refreshing...</div>", unsafe_allow_html=True)
    st.session_state.show_refresh_overlay = False

display_scores(st.session_state.selected_sport, formatted_date)
