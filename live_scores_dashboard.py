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
    </style>
""", unsafe_allow_html=True)

SPORTS = {
    "NFL (Football)": {"path": "football/nfl", "icon": "🏈"},
    "NBA (Basketball)": {"path": "basketball/nba", "icon": "🏀"},
    "MLB (Baseball)": {"path": "baseball/mlb", "icon": "⚾"},
    "NHL (Hockey)": {"path": "hockey/nhl", "icon": "💂"}
}

TEAM_COLORS = {
    "NE": "#002244", "DAL": "#003594", "GB": "#203731", "KC": "#E31837", "PHI": "#004C54",
    "SF": "#AA0000", "CHI": "#0B162A", "PIT": "#FFB612",
    "LAL": "#552583", "BOS": "#007A33", "GSW": "#1D428A", "MIA": "#98002E", "NYK": "#F58426",
    "NYY": "#003087", "LAD": "#005A9C", "CHC": "#0E3386", "HOU": "#EB6E1F",
    "NYR": "#0038A8", "TOR": "#00205B", "VGK": "#B4975A"
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
        t1, t2 = teams

        possession = comp.get("situation", {}).get("possession")
        on_first = comp.get("situation", {}).get("onFirst")
        on_second = comp.get("situation", {}).get("onSecond")
        on_third = comp.get("situation", {}).get("onThird")

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
            "clock": comp['status'].get("displayClock", ""),
            "on_first": on_first,
            "on_second": on_second,
            "on_third": on_third
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

        col1, col2, col3 = st.columns([4, 2, 4])
        with col1:
            st.image(t1['logo'], width=60)
            st.markdown(f"### {t1['name']}")
            st.markdown(f"<div class='{b1}'><strong>{t1['score']}</strong></div>", unsafe_allow_html=True)
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

        with col3:
            st.image(t2['logo'], width=60)
            st.markdown(f"### {t2['name']}")
            st.markdown(f"<div class='{b2}'><strong>{t2['score']}</strong></div>", unsafe_allow_html=True)
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
