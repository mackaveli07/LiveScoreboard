import streamlit as st
import requests
import time
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="Live Sports Scores", layout="wide")

# Animation CSS
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
    </style>
""", unsafe_allow_html=True)

SPORTS = {
    "NFL (Football)": {"path": "football/nfl", "icon": "🏈"},
    "NBA (Basketball)": {"path": "basketball/nba", "icon": "🏀"},
    "MLB (Baseball)": {"path": "baseball/mlb", "icon": "⚾"},
    "NHL (Hockey)": {"path": "hockey/nhl", "icon": "🛂"}
}

TEAM_COLORS = {
    # NFL
    "ARI": "#97233F", "ATL": "#A71930", "BAL": "#241773", "BUF": "#00338D", "CAR": "#0085CA",
    "CHI": "#0B162A", "CIN": "#FB4F14", "CLE": "#311D00", "DAL": "#003594", "DEN": "#002244",
    "DET": "#0076B6", "GB": "#203731", "HOU": "#03202F", "IND": "#002C5F", "JAX": "#006778",
    "KC": "#E31837", "LV": "#000000", "LAC": "#0080C6", "LAR": "#003594", "MIA": "#008E97",
    "MIN": "#4F2683", "NE": "#002244", "NO": "#D3BC8D", "NYG": "#0B2265", "NYJ": "#125740",
    "PHI": "#004C54", "PIT": "#FFB612", "SF": "#AA0000", "SEA": "#002244", "TB": "#D50A0A",
    "TEN": "#4B92DB", "WAS": "#773141",

    # NBA
    "ATL": "#E03A3E", "BOS": "#007A33", "BKN": "#000000", "CHA": "#1D1160", "CHI": "#CE1141",
    "CLE": "#860038", "DAL": "#00538C", "DEN": "#0E2240", "DET": "#C8102E", "GSW": "#1D428A",
    "HOU": "#CE1141", "IND": "#002D62", "LAC": "#C8102E", "LAL": "#552583", "MEM": "#5D76A9",
    "MIA": "#98002E", "MIL": "#00471B", "MIN": "#0C2340", "NOP": "#0C2340", "NYK": "#F58426",
    "OKC": "#007AC1", "ORL": "#0077C0", "PHI": "#006BB6", "PHX": "#1D1160", "POR": "#E03A3E",
    "SAC": "#5A2D81", "SAS": "#C4CED4", "TOR": "#CE1141", "UTA": "#002B5C", "WAS": "#002B5C",

    # MLB
    "ARI": "#A71930", "ATL": "#CE1141", "BAL": "#DF4601", "BOS": "#BD3039", "CHC": "#0E3386",
    "CIN": "#C6011F", "CLE": "#0F223E", "COL": "#333366", "CWS": "#27251F", "DET": "#0C2340",
    "HOU": "#EB6E1F", "KC": "#004687", "LAA": "#BA0021", "LAD": "#005A9C", "MIA": "#00A3E0",
    "MIL": "#12284B", "MIN": "#002B5C", "NYM": "#002D72", "NYY": "#003087", "OAK": "#003831",
    "PHI": "#E81828", "PIT": "#FDB827", "SD": "#2F241D", "SEA": "#0C2C56", "SF": "#FD5A1E",
    "STL": "#C41E3A", "TB": "#092C5C", "TEX": "#003278", "TOR": "#134A8E", "WSH": "#AB0003",

    # NHL
    "ANA": "#FC4C02", "ARI": "#8C2633", "BOS": "#FFB81C", "BUF": "#002654", "CGY": "#C8102E",
    "CAR": "#CC0000", "CHI": "#CF0A2C", "COL": "#6F263D", "CBJ": "#002654", "DAL": "#006847",
    "DET": "#CE1126", "EDM": "#041E42", "FLA": "#041E42", "LAK": "#111111", "MIN": "#154734",
    "MTL": "#AF1E2D", "NSH": "#FFB81C", "NJD": "#CE1126", "NYI": "#00539B", "NYR": "#0038A8",
    "OTT": "#E31837", "PHI": "#F74902", "PIT": "#FCB514", "SJS": "#006D75", "SEA": "#99D9D9",
    "STL": "#002F87", "TBL": "#002868", "TOR": "#00205B", "VAN": "#00205B", "VGK": "#B4975A",
    "WSH": "#041E42", "WPG": "#041E42"
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
        b1 = " blinking" if prev[0] != t1['score'] and prev[0] is not None else ""
        b2 = " blinking" if prev[1] != t2['score'] and prev[1] is not None else ""

        flash1 = f"<div class='scoring-indicator' style='background:{TEAM_COLORS.get(t1['abbreviation'], '#ccc')}'>{t1['score']}</div>" if b1 else f"<strong>{t1['score']}</strong>"
        flash2 = f"<div class='scoring-indicator' style='background:{TEAM_COLORS.get(t2['abbreviation'], '#ccc')}'>{t2['score']}</div>" if b2 else f"<strong>{t2['score']}</strong>"

        col1, col2, col3 = st.columns([4, 2, 4])
        with col1:
            st.image(t1['logo'], width=60)
            st.markdown(f"### {t1['name']}")
            st.markdown(flash1, unsafe_allow_html=True)
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
            st.markdown(flash2, unsafe_allow_html=True)
            if t2['possession']:
                st.markdown("🏈 Possession")

        st.markdown("---")

# Sidebar controls
st.sidebar.title("Controls")
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False

if st.sidebar.button(":arrows_counterclockwise: Refresh Now"):
    st.cache_data.clear()
    st.rerun()

if st.sidebar.button(":pause_button: Toggle Auto-Refresh"):
    st.session_state.auto_refresh = not st.session_state.auto_refresh

# Main content
st.title(":classical_building: Live Sports Scores Dashboard")
st.markdown("Real-time updates with team logos and stats.")

selected_date = st.sidebar.date_input("Select date:", datetime.today())
selected_sport = st.sidebar.selectbox("Choose a sport:", list(SPORTS.keys()))
formatted_date = selected_date.strftime("%Y%m%d")

display_scores(selected_sport, formatted_date)

if st.session_state.auto_refresh:
    time.sleep(2)
    st.cache_data.clear()
    st.rerun()
