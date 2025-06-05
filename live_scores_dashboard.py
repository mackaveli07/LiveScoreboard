import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Live Sports Ticker", layout="wide")

SPORTS = {
    "NFL (Football)": "football/nfl",
    "NBA (Basketball)": "basketball/nba",
    "MLB (Baseball)": "baseball/mlb",
    "NHL (Hockey)": "hockey/nhl"
}

def sanitize_hex(color):
    return f"#{color}" if color and len(color) == 6 else "#000000"

def get_scores_with_colors(sport_path):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        st.error(f"Failed to fetch data: {e}")
        return []

    games = data.get("events", [])
    results = []

    for game in games:
        competition = game['competitions'][0]
        status = competition['status']['type']['shortDetail']
        teams = competition['competitors']

        if len(teams) != 2:
            continue

        game_data = {
            "status": status,
            "teams": [],
            "id": game["id"]
        }

        for team in teams:
            team_info = team['team']
            colors = sanitize_hex(team_info.get("color"))
            alt_color = sanitize_hex(team_info.get("alternateColor"))
            game_data["teams"].append({
                "name": team_info['displayName'],
                "score": team.get('score', '0'),
                "logo": team_info['logo'],
                "color": colors,
                "alt_color": alt_color,
                "abbreviation": team_info['abbreviation']
            })

        results.append(game_data)
    return results

def set_background_color():
    st.markdown("""
        <style>
        .stApp {
            background-color: #e28743;
        }
        </style>
    """, unsafe_allow_html=True)

set_background_color()

def display_scores(sport_name):
    st.markdown(f"### 🏆 {sport_name}")
    scores = get_scores_with_colors(SPORTS[sport_name])
    if not scores:
        st.info("No live or recent games currently.")
        return

    st.markdown(
        """
        <style>
        .ticker-container {
            display: flex;
            overflow-x: auto;
            padding: 10px 0;
            white-space: nowrap;
        }
        .ticker-card {
            background-color: #fff;
            border-radius: 10px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
            padding: 10px 15px;
            margin-right: 10px;
            display: inline-block;
            min-width: 320px;
            max-width: 400px;
        }
        .team {
            display: inline-block;
            width: 48%;
            vertical-align: top;
            text-align: center;
        }
        .team img {
            height: 40px;
            margin-bottom: 5px;
        }
        .team-name {
            font-size: 14px;
            font-weight: bold;
        }
        .score-box {
            font-size: 22px;
            font-weight: bold;
            border-radius: 6px;
            padding: 4px 10px;
            display: inline-block;
            margin-top: 5px;
        }
        .status-text {
            text-align: center;
            font-size: 12px;
            margin-top: 8px;
            color: #444;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    ticker_html = '<div class="ticker-container">'
    for game in scores:
        team1, team2 = game["teams"]

        card_html = f"""
        <div class="ticker-card">
            <div class="team">
                <img src="{team1['logo']}" />
                <div class="team-name" style="color:{team1['color']}">{team1['name']}</div>
                <div class="score-box" style="background:{team1['color']}; color:{team1['alt_color']}">{team1['score']}</div>
            </div>
            <div class="team">
                <img src="{team2['logo']}" />
                <div class="team-name" style="color:{team2['color']}">{team2['name']}</div>
                <div class="score-box" style="background:{team2['color']}; color:{team2['alt_color']}">{team2['score']}</div>
            </div>
            <div class="status-text">🕒 {game['status']}</div>
        </div>
        """
        ticker_html += card_html

    ticker_html += '</div>'
    st.markdown(ticker_html, unsafe_allow_html=True)

# ⏱️ Auto-refresh interval
refresh_interval = st.sidebar.slider("Auto-refresh every (seconds):", 10, 60, 30)
st_autorefresh(interval=refresh_interval * 1000, key="ticker_refresh")

# 🧭 UI
st.title("📺 Live Sports Ticker Dashboard")
st.markdown("Real-time scores across leagues in a scrolling ticker layout.")

selected_sports = st.sidebar.multiselect(
    "Select sports to display:",
    list(SPORTS.keys()),
    default=list(SPORTS.keys())
)

for sport in selected_sports:
    display_scores(sport)
