import streamlit as st
import requests

st.set_page_config(page_title="Live Sports Scores", layout="wide")

SPORTS = {
    "NFL (Football)": "football/nfl",
    "NBA (Basketball)": "basketball/nba",
    "MLB (Baseball)": "baseball/mlb",
    "NHL (Hockey)": "hockey/nhl"
}

if "previous_scores" not in st.session_state:
    st.session_state.previous_scores = {}

def sanitize_hex(color):
    return f"#{color}" if color and len(color) == 6 else "#000000"

def set_custom_theme():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');

    .stApp {
        background-image: url('https://i.imgur.com/qZ1G6XG.jpg');
        background-size: cover;
        background-attachment: fixed;
        font-family: 'Bebas Neue', sans-serif;
    }

    .main-title {
        font-size: 64px;
        text-align: center;
        color: white;
        text-shadow: 3px 3px 6px #000;
        margin-bottom: 10px;
    }

    .score-box {
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        border-radius: 16px;
        padding: 10px;
        margin: 10px 0;
    }

    .score {
        font-size: 30px;
        font-weight: bold;
        padding: 8px 16px;
        border-radius: 10px;
        margin-top: 5px;
        display: inline-block;
    }

    .blink {
        animation: blinker 1s linear infinite;
    }

    @keyframes blinker {
        50% { opacity: 0; }
    }
    </style>
    """, unsafe_allow_html=True)

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

def get_game_stats(game_id, sport_path):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/summary?event={game_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        st.error(f"Failed to fetch game stats: {e}")
        return None

    stats = []
    for team in data.get("boxscore", {}).get("teams", []):
        team_name = team.get("team", {}).get("displayName", "Unknown Team")
        lines = []
        for cat in team.get("statistics", []):
            label = cat.get("label", "Stat")
            stat = cat.get("stats", ["-"])[0]
            lines.append(f"**{label}**: {stat}")
        stats.append((team_name, lines))

    return stats

def display_scores(sport_name, logo_size):
    st.subheader(f"🏆 {sport_name}")
    scores = get_scores_with_colors(SPORTS[sport_name])
    if not scores:
        st.info("No live or recent games currently.")
        return

    for game in scores:
        team1, team2 = game["teams"]
        with st.expander(f"{team1['name']} vs {team2['name']} - {game['status']}", expanded=False):
            col1, col2, col3 = st.columns([4, 2, 4])

            # Team 1
            with col1:
                st.image(team1["logo"], width=logo_size)
                st.markdown(
                    f"<div style='font-size: 20px; font-weight: bold; color:{team1['color']}'>{team1['name']}</div>",
                    unsafe_allow_html=True,
                )
                score_key1 = f"{game['id']}_1"
                previous_score1 = st.session_state.previous_scores.get(score_key1, "")
                current_score1 = team1["score"]
                changed1 = previous_score1 != current_score1
                st.session_state.previous_scores[score_key1] = current_score1

                st.markdown(
                    f"<div class='score {'blink' if changed1 else ''}' style='background-color:{team1['color']}; color:{team1['alt_color']}'>{current_score1}</div>",
                    unsafe_allow_html=True,
                )

            # VS & Toggle
            with col2:
                st.markdown("<div style='text-align:center; font-size: 18px; color: gray;'>VS</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:center; font-size: 14px; color: #ccc;'>Status:<br><strong>{game['status']}</strong></div>", unsafe_allow_html=True)
                toggle_key = f"show_stats_{game['id']}"
                show = st.toggle("📊 View Stats", key=toggle_key)

            # Team 2
            with col3:
                st.image(team2["logo"], width=logo_size)
                st.markdown(
                    f"<div style='font-size: 20px; font-weight: bold; color:{team2['color']}'>{team2['name']}</div>",
                    unsafe_allow_html=True,
                )
                score_key2 = f"{game['id']}_2"
                previous_score2 = st.session_state.previous_scores.get(score_key2, "")
                current_score2 = team2["score"]
                changed2 = previous_score2 != current_score2
                st.session_state.previous_scores[score_key2] = current_score2

                st.markdown(
                    f"<div class='score {'blink' if changed2 else ''}' style='background-color:{team2['color']}; color:{team2['alt_color']}'>{current_score2}</div>",
                    unsafe_allow_html=True,
                )

            if show:
                stats = get_game_stats(game["id"], SPORTS[sport_name])
                if stats:
                    st.markdown(f"### 📈 Game Stats: {team1['name']} vs {team2['name']}")
                    stat_cols = st.columns(2)
                    for i, (team_name, lines) in enumerate(stats):
                        with stat_cols[i]:
                            st.markdown(f"#### {team_name}")
                            for line in lines:
                                st.markdown(line)

# Run App
set_custom_theme()
st.markdown("<div class='main-title'>📺 Live Sports Scores Dashboard</div>", unsafe_allow_html=True)

selected_sports = st.sidebar.multiselect(
    "Select sports to display:",
    list(SPORTS.keys()),
    default=list(SPORTS.keys())
)

logo_size = st.sidebar.slider("Team Logo Size", min_value=40, max_value=100, value=60)
refresh_rate = st.sidebar.slider("Auto-refresh every (seconds):", 10, 60, 30)

# Manual refresh logic
import time
last_refresh = st.session_state.get("last_refresh", 0)
if time.time() - last_refresh >= refresh_rate:
    st.session_state.last_refresh = time.time()

for sport in selected_sports:
    display_scores(sport, logo_size)

# Add an auto-refresh meta tag for actual auto-refresh behavior on Streamlit Cloud
st.markdown(f"""
    <meta http-equiv="refresh" content="{refresh_rate}">
""", unsafe_allow_html=True)
