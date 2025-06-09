import streamlit as st
import requests
import time
from datetime import datetime
import streamlit.components.v1 as components
from team_colors_all_leagues import TEAM_COLORS  # External file for team colors

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
TEAM_COLORS = {
    "NE": "#002244", "MIA": "#008E97", "BUF": "#00338D", "NYJ": "#125740",
    "DAL": "#041E42", "PHI": "#004C54", "NYG": "#0B2265", "WAS": "#773141",
    "KC": "#E31837", "DEN": "#FB4F14", "LV": "#000000", "LAC": "#002A5E",
    "GB": "#203731", "CHI": "#0B162A", "MIN": "#4F2683", "DET": "#0076B6",
    "BAL": "#241773", "PIT": "#FFB612", "CLE": "#311D00", "CIN": "#FB4F14",
    "SF": "#AA0000", "SEA": "#002244", "LAR": "#003594", "ARI": "#97233F",
    "ATL": "#A71930", "NO": "#D3BC8D", "CAR": "#0085CA", "TB": "#D50A0A",
    "IND": "#002C5F", "TEN": "#4B92DB", "JAX": "#006778", "HOU": "#03202F",
    "BOS": "#007A33", "BKN": "#000000", "NYK": "#006BB6", "PHI": "#006BB6",
    "TOR": "#CE1141", "CHI": "#CE1141", "CLE": "#860038", "DET": "#C8102E",
    "IND": "#FDBB30", "MIL": "#00471B", "ATL": "#E03A3E", "CHA": "#1D1160",
    "MIA": "#98002E", "ORL": "#0077C0", "WAS": "#002B5C", "DEN": "#0E2240",
    "MIN": "#0C2340", "OKC": "#007AC1", "POR": "#E03A3E", "UTA": "#002B5C",
    "GSW": "#1D428A", "LAC": "#C8102E", "LAL": "#552583", "PHX": "#1D1160",
    "SAC": "#5A2D81", "DAL": "#00538C", "HOU": "#CE1141", "MEM": "#5D76A9",
    "NOP": "#0C2340", "SAS": "#C4CED4",
    "NYY": "#003087", "BOS": "#BD3039", "TOR": "#134A8E", "BAL": "#DF4601",
    "TB": "#092C5C", "CHW": "#27251F", "CLE": "#0C2340", "DET": "#0C2340",
    "KC": "#004687", "MIN": "#002B5C", "HOU": "#EB6E1F", "LAA": "#BA0021",
    "OAK": "#003831", "SEA": "#005C5C", "TEX": "#003278", "ATL": "#CE1141",
    "MIA": "#00A3E0", "NYM": "#002D72", "PHI": "#E81828", "WSH": "#AB0003",
    "CHC": "#0E3386", "CIN": "#C6011F", "MIL": "#12284B", "PIT": "#FDB827",
    "STL": "#C41E3A", "ARI": "#A71930", "COL": "#33006F", "LAD": "#005A9C",
    "SD": "#2F241D", "SF": "#FD5A1E",
    "ANA": "#FC4C02", "BOS": "#FFB81C", "BUF": "#002654", "CGY": "#C8102E",
    "CAR": "#CC0000", "CHI": "#CF0A2C", "COL": "#6F263D", "CBJ": "#002654",
    "DAL": "#006847", "DET": "#CE1126", "EDM": "#041E42", "FLA": "#041E42",
    "LAK": "#111111", "MIN": "#154734", "MTL": "#AF1E2D", "NSH": "#FFB81C",
    "NJD": "#CE1126", "NYI": "#00539B", "NYR": "#0038A8", "OTT": "#E31837",
    "PHI": "#F74902", "PIT": "#FCB514", "SJS": "#006D75", "SEA": "#001628",
    "STL": "#002F87", "TBL": "#002868", "TOR": "#00205B", "VAN": "#00205B",
    "VGK": "#B4975A", "WSH": "#041E42", "WPG": "#041E42"
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
        b1 = prev[0] != t1['score'] and prev[0] is not None
        b2 = prev[1] != t2['score'] and prev[1] is not None

        flash1 = f"<div class='score-blink' style='color:{TEAM_COLORS.get(t1['abbreviation'], '#000')}'>{t1['score']}</div>" if b1 else f"<strong>{t1['score']}</strong>"
        flash2 = f"<div class='score-blink' style='color:{TEAM_COLORS.get(t2['abbreviation'], '#000')}'>{t2['score']}</div>" if b2 else f"<strong>{t2['score']}</strong>"

        color1 = TEAM_COLORS.get(t1['abbreviation'], '#ddd')
        color2 = TEAM_COLORS.get(t2['abbreviation'], '#ccc')
        box_style = f"background: linear-gradient(to right, {color1}, {color2}); padding: 1em; border-radius: 12px; box-shadow: 0 0 10px rgba(0,0,0,0.1); margin-bottom: 1em;"

        with st.container():
            st.markdown(f"<div class='score-box' style='{box_style}'>", unsafe_allow_html=True)
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
            st.markdown("</div>", unsafe_allow_html=True)
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

