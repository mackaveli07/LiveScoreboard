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
    </style>
""", unsafe_allow_html=True)

from team_colors import TEAM_COLORS  # Assuming this file contains full dictionary of team colors

SPORTS = {
    "NFL (Football)": {"path": "football/nfl", "icon": "🏈"},
    "NBA (Basketball)": {"path": "basketball/nba", "icon": "🏀"},
    "MLB (Baseball)": {"path": "baseball/mlb", "icon": "⚾"},
    "NHL (Hockey)": {"path": "hockey/nhl", "icon": "🎲"}
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

        status_type = comp['status']['type']
        if show_live_only and status_type['state'] not in ['in', 'pre']:
            continue

        situation = comp.get("situation", {})
        possession = situation.get("possession")
        on_first = situation.get("onFirst")
        on_second = situation.get("onSecond")
        on_third = situation.get("onThird")
        balls = situation.get("balls")
        strikes = situation.get("strikes")
        outs = situation.get("outs")
        pitcher = situation.get("pitcher", {}).get("athlete", {}).get("displayName")
        next_batter = situation.get("batter", {}).get("athlete", {}).get("displayName")
        on_deck = situation.get("onDeck", {}).get("athlete", {}).get("displayName")
        in_hole = situation.get("inHole", {}).get("athlete", {}).get("displayName")

        results.append({
            "id": event['id'],
            "status": status_type['shortDetail'],
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
            "outs": outs,
            "pitcher": pitcher,
            "next_batter": next_batter,
            "on_deck": on_deck,
            "in_hole": in_hole
        })

    return results

st.sidebar.title("Controls")
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False
if "show_live_only" not in st.session_state:
    st.session_state.show_live_only = True

refresh_now = st.sidebar.button("\U0001f504 Refresh Now")
if refresh_now:
    st.cache_data.clear()
    st.rerun()

toggle_refresh = st.sidebar.button("⏯ Toggle Auto-Refresh")
if toggle_refresh:
    st.session_state.auto_refresh = not st.session_state.auto_refresh

show_live_only = st.sidebar.checkbox("Show only live/in-progress games", value=True)

st.title("\U0001f3df Live Sports Scoreboard")
st.markdown("Live updates with team logos, stats, and animations.")

selected_date = st.sidebar.date_input("Select date:", datetime.today())
selected_sport = st.sidebar.selectbox("Choose a sport:", list(SPORTS.keys()))
formatted_date = selected_date.strftime("%Y%m%d")

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
                if game['pitcher']:
                    st.markdown(f"**Pitcher:** {game['pitcher']}")
                if game['next_batter']:
                    st.markdown(f"**Next Batter:** {game['next_batter']}")
                if game['on_deck']:
                    st.markdown(f"**On Deck:** {game['on_deck']}")
                if game['in_hole']:
                    st.markdown(f"**In Hole:** {game['in_hole']}")

        with col3:
            st.image(t2['logo'], width=60)
            st.markdown(f"### {t2['name']}")
            st.markdown(score2_html, unsafe_allow_html=True)
            if t2['possession']:
                st.markdown("🏈 Possession")

        st.markdown("---")

display_scores(selected_sport, formatted_date)

if st.session_state.auto_refresh:
    time.sleep(2)
    st.cache_data.clear()
    st.rerun()
