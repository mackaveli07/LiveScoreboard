import streamlit as st
import requests
from PIL import Image
from io import BytesIO
from colorthief import ColorThief
import tempfile

st.set_page_config(page_title="Live Sports Scores Dashboard", layout="wide")

SPORTS = {
    "NFL (Football)": {"path": "football/nfl"},
    "NBA (Basketball)": {"path": "basketball/nba"},
    "MLB (Baseball)": {"path": "baseball/mlb"},
    "NHL (Hockey)": {"path": "hockey/nhl"},
}

def get_dominant_color_from_url(url):
    try:
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            image.save(tmp.name)
            color_thief = ColorThief(tmp.name)
            dominant_color = color_thief.get_color(quality=1)
            return f'rgb{dominant_color}'
    except:
        return 'gray'

def get_scores(sport_path):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard"
    try:
        response = requests.get(url)
        data = response.json()
        return data.get("events", [])
    except:
        return []

def get_game_stats(game_id, sport_path):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/summary?event={game_id}"
    try:
        response = requests.get(url)
        data = response.json()
        stats = []
        for team in data.get("boxscore", {}).get("teams", []):
            team_name = team.get("team", {}).get("displayName", "Unknown")
            lines = []
            for cat in team.get("statistics", []):
                label = cat.get("label", "Stat")
                stat = cat.get("stats", ["-"])[0]
                lines.append(f"**{label}**: {stat}")
            stats.append((team_name, lines))
        return stats
    except:
        return []

def display_scores(sport_name, logo_size):
    sport_config = SPORTS[sport_name]
    events = get_scores(sport_config["path"])
    st.subheader(f"🏆 {sport_name}")

    for event in events:
        comp = event['competitions'][0]
        teams = comp['competitors']
        status = comp['status']['type']['shortDetail']
        period = comp['status'].get('period', '')

        if len(teams) != 2:
            continue

        team1 = teams[0]['team']
        team2 = teams[1]['team']
        team1_score = teams[0].get("score", "0")
        team2_score = teams[1].get("score", "0")

        team1_logo = team1.get("logo", "")
        team2_logo = team2.get("logo", "")

        team1_color = get_dominant_color_from_url(team1_logo)
        team2_color = get_dominant_color_from_url(team2_logo)

        with st.expander(f"{team1['displayName']} vs {team2['displayName']} - {status}"):
            col1, col2, col3 = st.columns([4, 2, 4])

            with col1:
                st.image(team1_logo, width=logo_size)
                st.markdown(f"<div style='border: 4px solid {team1_color}; padding: 8px; font-weight:bold;'>{team1['displayName']}<br><span style='font-size: 28px;'>{team1_score}</span></div>", unsafe_allow_html=True)

            with col2:
                st.markdown(f"<div style='text-align:center;'>VS</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:center;'>Status:<br><strong>{status}</strong></div>", unsafe_allow_html=True)
                if period:
                    st.markdown(f"<div style='text-align:center;'>Period: {period}</div>", unsafe_allow_html=True)
                if st.toggle("📊 View Stats", key=f"stats_{event['id']}"):
                    stats = get_game_stats(event['id'], sport_config["path"])
                    if stats:
                        stat_cols = st.columns(2)
                        for i, (team_name, lines) in enumerate(stats):
                            with stat_cols[i]:
                                st.markdown(f"#### {team_name}")
                                for line in lines:
                                    st.markdown(line)

            with col3:
                st.image(team2_logo, width=logo_size)
                st.markdown(f"<div style='border: 4px solid {team2_color}; padding: 8px; font-weight:bold;'>{team2['displayName']}<br><span style='font-size: 28px;'>{team2_score}</span></div>", unsafe_allow_html=True)

# App layout
st.title("📺 Live Sports Scores Dashboard")
st.markdown("Real-time updates with team logos, stats, dynamic color themes, and ESPN data.")

selected_sports = st.sidebar.multiselect(
    "Select sports to display:",
    list(SPORTS.keys()),
    default=list(SPORTS.keys())
)
logo_size = st.sidebar.slider("Team Logo Size", 40, 100, 60)

for sport in selected_sports:
    display_scores(sport, logo_size)
