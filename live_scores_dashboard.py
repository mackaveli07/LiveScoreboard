import streamlit as st
import requests
import time
from datetime import datetime
import streamlit.components.v1 as components

try:
    from team_colors_all_leagues import TEAM_COLORS
except ImportError:
    TEAM_COLORS = {}
    st.warning("Could not import TEAM_COLORS. Please ensure 'team_colors_all_leagues.py' exists and defines TEAM_COLORS.")

st.set_page_config(page_title="Live Sports Scores", layout="wide")

# Animation and Styling CSS
st.markdown("""
    <style>
    .blinking {
        animation: blinker 1s linear infinite;
    }
    @keyframes blinker {
        50% { opacity: 0.5; }
    }
    .diamond {
        width: 50px;
        height: 50px;
        position: relative;
        margin: 10px auto;
    }
    .base {
        width: 12px;
        height: 12px;
        background-color: lightgray;
        position: absolute;
        transform: rotate(45deg);
    }
    .base.occupied {
        background-color: green;
    }
    .first { bottom: 0; right: 0; transform: translate(50%, 50%) rotate(45deg); }
    .second { top: 0; left: 50%; transform: translate(-50%, -50%) rotate(45deg); }
    .third { bottom: 0; left: 0; transform: translate(-50%, 50%) rotate(45deg); }
    .scoring-indicator {
        animation: flash 1s infinite;
        font-weight: bold;
        padding: 0.25em 0.5em;
        border-radius: 5px;
        display: inline-block;
    }
    @keyframes flash {
        0% { opacity: 1; }
        50% { opacity: 0.2; }
        100% { opacity: 1; }
    }
    .score-blink {
        animation: blinkScore 1s step-start 0s infinite;
    }
    @keyframes blinkScore {
        0% { opacity: 1; }
        50% { opacity: 0; }
        100% { opacity: 1; }
    }
    </style>
""", unsafe_allow_html=True)

SPORTS = {
    "NFL (Football)": {"path": "football/nfl", "icon": "🏈"},
    "NBA (Basketball)": {"path": "basketball/nba", "icon": "🏀"},
    "MLB (Baseball)": {"path": "baseball/mlb", "icon": "⚾"},
    "NHL (Hockey)": {"path": "hockey/nhl", "icon": "🛂"}
}

score_cache = {}

@st.cache_data(ttl=30)
def get_scores(sport_path, date=None):
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
        comp = event.get('competitions', [{}])[0]
        teams = comp.get('competitors', [])
        if len(teams) != 2:
            continue

        home = next((t for t in teams if t.get('homeAway') == 'home'), None)
        away = next((t for t in teams if t.get('homeAway') == 'away'), None)

        if not home or not away:
            continue

        situation = comp.get("situation", {})
        possession = situation.get("possession")
        on_first = situation.get("onFirst")
        on_second = situation.get("onSecond")
        on_third = situation.get("onThird")
        balls = situation.get("balls")
        strikes = situation.get("strikes")
        outs = situation.get("outs")

        results.append({
            "id": event.get('id'),
            "status": comp.get('status', {}).get('type', {}).get('shortDetail', ''),
            "teams": [
                {
                    "name": away['team'].get('displayName', 'Away'),
                    "score": away.get('score', '0'),
                    "logo": away['team'].get('logo', ''),
                    "abbreviation": away['team'].get('abbreviation', 'UNK'),
                    "possession": away['team'].get('id') == possession
                },
                {
                    "name": home['team'].get('displayName', 'Home'),
                    "score": home.get('score', '0'),
                    "logo": home['team'].get('logo', ''),
                    "abbreviation": home['team'].get('abbreviation', 'UNK'),
                    "possession": home['team'].get('id') == possession
                }
            ],
            "period": comp.get('status', {}).get("period", ""),
            "clock": comp.get('status', {}).get("displayClock", ""),
            "on_first": on_first,
            "on_second": on_second,
            "on_third": on_third,
            "balls": balls,
            "strikes": strikes,
            "outs": outs
        })

    return results
