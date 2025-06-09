import streamlit as st
import requests
import time
from datetime import datetime

st.set_page_config(page_title="Live Sports Scores", layout="wide")

# CSS styles for animations and diamond
st.markdown("""
    <style>
    .blinking {
        animation: blinker 1s linear infinite;
    }
    @keyframes blinker {
        50% { opacity: 0.5; }
    }
    @keyframes flash {
        0% { background-color: white; color: black; }
        50% { background-color: black; color: white; }
        100% { background-color: white; color: black; }
    }
    .score-box {
        padding: 8px 12px;
        border-radius: 10px;
        font-weight: bold;
        font-size: 24px;
        display: inline-block;
        min-width: 60px;
        text-align: center;
        margin-top: 4px;
    }
    .flash {
        animation: flash 1s infinite;
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
    .score-container {
        background: linear-gradient(to right, var(--t1-color), var(--t2-color));
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 20px;
        border: 3px solid #ccc;
    }
    </style>
""", unsafe_allow_html=True)

SPORTS = {
    "NFL (Football)": {"path": "football/nfl", "icon": "🏈"},
    "NBA (Basketball)": {"path": "basketball/nba", "icon": "🏀"},
    "MLB (Baseball)": {"path": "baseball/mlb", "icon": "⚾"},
    "NHL (Hockey)": {"path": "hockey/nhl", "icon": "🏂"}
}

TEAM_COLORS = {
    "Arizona Diamondbacks": {"primary": "#A71930"},
    "Atlanta Braves": {"primary": "#CE1141"},
    "Baltimore Orioles": {"primary": "#DF4601"},
    "Boston Red Sox": {"primary": "#BD3039"},
    "Chicago White Sox": {"primary": "#27251F"},
    "Chicago Cubs": {"primary": "#0E3386"},
    "Cincinnati Reds": {"primary": "#C6011F"},
    "Cleveland Guardians": {"primary": "#0C2340"},
    "Colorado Rockies": {"primary": "#333366"},
    "Detroit Tigers": {"primary": "#0C2340"},
    "Houston Astros": {"primary": "#002D62"},
    "Kansas City Royals": {"primary": "#004687"},
    "Los Angeles Angels": {"primary": "#BA0021"},
    "Los Angeles Dodgers": {"primary": "#005A9C"},
    "Miami Marlins": {"primary": "#00A3E0"},
    "Milwaukee Brewers": {"primary": "#12284B"},
    "Minnesota Twins": {"primary": "#002B5C"},
    "New York Yankees": {"primary": "#003087"},
    "New York Mets": {"primary": "#002D72"},
    "Oakland Athletics": {"primary": "#003831"},
    "Philadelphia Phillies": {"primary": "#E81828"},
    "Pittsburgh Pirates": {"primary": "#FDB827"},
    "San Diego Padres": {"primary": "#2F241D"},
    "San Francisco Giants": {"primary": "#FD5A1E"},
    "Seattle Mariners": {"primary": "#005C5C"},
    "St. Louis Cardinals": {"primary": "#C41E3A"},
    "Tampa Bay Rays": {"primary": "#092C5C"},
    "Texas Rangers": {"primary": "#003278"},
    "Toronto Blue Jays": {"primary": "#134A8E"},
    "Washington Nationals": {"primary": "#AB0003"},
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
        comp = event['competitions'][0]
        teams = comp['competitors']
        if len(teams) != 2:
            continue

        home = [t for t in teams if t['homeAway'] == 'home'][0]
        away = [t for t in teams if t['homeAway'] == 'away'][0]

        situation = comp.get("situation", {})
        possession = situation.get("possession")
        on_first = situation.get("onFirst")
        on_second = situation.get("onSecond")
        on_third = situation.get("onThird")
        balls = situation.get("balls")
        strikes = situation.get("strikes")
        outs = situation.get("outs")

        results.append({
            "id": event['id'],
            "status": comp['status']['type']['shortDetail'],
            "teams": [
                {
                    "name": away['team']['displayName'],
                    "score": away['score'],
                    "logo": away['team']['logo'],
                    "abbreviation": away['team']['abbreviation'],
                    "possession": away['team']['id'] == possession
                },
                {
                    "name": home['team']['displayName'],
                    "score": home['score'],
                    "logo": home['team']['logo'],
                    "abbreviation": home['team']['abbreviation'],
                    "possession": home['team']['id'] == possession
                }
            ],
            "period": comp['status'].get("period", ""),
            "clock": comp['status'].get("displayClock", ""),
            "on_first": on_first,
            "on_second": on_second,
            "on_third": on_third,
            "balls": balls,
            "strikes": strikes,
            "outs": outs
        })

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

        t1_color = TEAM_COLORS.get(t1['name'], {"primary": "#444"})["primary"]
        t2_color = TEAM_COLORS.get(t2['name'], {"primary": "#444"})["primary"]

        t1_changed = prev[0] != t1['score'] and prev[0] is not None
        t2_changed = prev[1] != t2['score'] and prev[1] is not None

        score1_html = f"<div class='score-box {'flash' if t1_changed else ''}' style='background:{t1_color}; color:white'>{t1['score']}</div>"
        score2_html = f"<div class='score-box {'flash' if t2_changed else ''}' style='background:{t2_color}; color:white'>{t2['score']}</div>"

        st.markdown(
            f"""
            <div class='score-container' style="--t1-color: {t1_color}; --t2-color: {t2_color};">
            """,
            unsafe_allow_html=True
        )

        col1, col2, col3 = st.columns([4, 2, 4])
        with col1:
            st.image(t1['logo'], width=60)
            st.markdown(f"### {t1['name']}")
            st.markdown(score1_html, unsafe_allow_html=True)
            if t1['possession']:
                st.markdown("🏈 Possession")

        with col2:
            st.markdown(f"### VS")
            st.markdown(f"**{game['status']}**")
            if sport_name != "MLB (Baseball)":
                st.markdown(f"Period: {game['period']}")
                st.markdown(f"Clock: {game['clock']}")
            else:
                st.markdown(f"Inning: {game['period']}")
                diamond_html = f"""
                <div class='diamond'>
                    <div class='base second {'occupied' if game['on_second'] else ''}'></div>
                    <div class='base third {'occupied' if game['on_third'] else ''}'></div>
                    <div class='base first {'occupied' if game['on_first'] else ''}'></div>
                </div>
                """
                st.markdown(diamond_html, unsafe_allow_html=True)
                st.markdown(f"**Outs:** {game['outs']}")
                st.markdown(f"**Balls:** {game['balls']}  **Strikes:** {game['strikes']}")

        with col3:
            st.image(t2['logo'], width=60)
            st.markdown(f"### {t2['name']}")
            st.markdown(score2_html, unsafe_allow_html=True)
            if t2['possession']:
                st.markdown("🏈 Possession")

        st.markdown("</div>", unsafe_allow_html=True)

# Sidebar controls
st.sidebar.title("Controls")
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False

if st.sidebar.button("🔄 Refresh Now"):
    st.cache_data.clear()
    st.rerun()

if st.sidebar.button("⎯ Toggle Auto-Refresh"):
    st.session_state.auto_refresh = not st.session_state.auto_refresh

# Main layout
st.title("🏟 Live Sports Scoreboard")
st.markdown("Live updates with team logos, stats, and animations.")

selected_date = st.sidebar.date_input("Select date:", datetime.today())
selected_sport = st.sidebar.selectbox("Choose a sport:", list(SPORTS.keys()))
formatted_date = selected_date.strftime("%Y%m%d")

display_scores(selected_sport, formatted_date)

if st.session_state.auto_refresh:
    time.sleep(2)
    st.cache_data.clear()
    st.rerun()
