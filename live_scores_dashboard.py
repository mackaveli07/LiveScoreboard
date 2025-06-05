import streamlit as st
import requests
import time

st.set_page_config(page_title="Live Sports Scores", layout="wide")

SPORTS = {
    "NFL (Football)": "football/nfl",
    "NBA (Basketball)": "basketball/nba",
    "MLB (Baseball)": "baseball/mlb",
    "NHL (Hockey)": "hockey/nhl"
}

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

        game_data = {
            "status": status,
            "teams": [],
            "id": game["id"]
        }

        for team in teams:
            team_info = team['team']
            colors = team_info.get("color") or "000000"
            alt_color = team_info.get("alternateColor") or "FFFFFF"
            game_data["teams"].append({
                "name": team_info['displayName'],
                "score": team.get('score', '0'),
                "logo": team_info['logo'],
                "color": f"#{colors}",
                "alt_color": f"#{alt_color}",
                "abbreviation": team_info['abbreviation']
            })

        results.append(game_data)
    return results


def set_background_color():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #f0f2f6;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

set_background_color()

def get_game_stats(game_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={game_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        st.error(f"Failed to fetch game stats: {e}")
        return None

    stats = []
    for team in data.get("boxscore", {}).get("teams", []):
        team_name = team["team"]["displayName"]
        lines = [f"**{category['label']}**: {category['stats'][0]}" for category in team["statistics"]]
        stats.append((team_name, lines))

    return stats

def display_scores(sport_name, logo_size):
    st.subheader(f"🏆 {sport_name}")
    scores = get_scores_with_colors(SPORTS[sport_name])
    if not scores:
        st.info("No live or recent games currently.")
        return

    for game in scores:
        with st.container():
            col1, col2, col3 = st.columns([4, 2, 4])
            team1, team2 = game["teams"]

            with col1:
                st.image(team1["logo"], width=logo_size)
                st.markdown(
                    f"<div style='font-size: 20px; font-weight: bold; color:{team1['color']}'>{team1['name']}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div style='background-color:{team1['color']}; color:{team1['alt_color']}; padding: 6px 12px; display:inline-block; font-size: 24px; border-radius: 8px; font-weight: bold;'>{team1['score']}</div>",
                    unsafe_allow_html=True,
                )

            with col2:
                st.markdown("<div style='text-align:center; font-size: 16px; color: gray;'>VS</div>", unsafe_allow_html=True)
                st.markdown(
                    f"<div style='text-align:center; font-size: 14px; color: #666;'>Status:<br><strong>{game['status']}</strong></div>",
                    unsafe_allow_html=True,
                )

                if st.button(f"📊 View Stats", key=f"stats_btn_{game['id']}"):
                    if st.session_state.get("show_stats") == game["id"]:
                        st.session_state["show_stats"] = None  # Collapse
                    else:
                        st.session_state["show_stats"] = game["id"]  # Expand

            with col3:
                st.image(team2["logo"], width=logo_size)
                st.markdown(
                    f"<div style='font-size: 20px; font-weight: bold; color:{team2['color']}'>{team2['name']}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div style='background-color:{team2['color']}; color:{team2['alt_color']}; padding: 6px 12px; display:inline-block; font-size: 24px; border-radius: 8px; font-weight: bold;'>{team2['score']}</div>",
                    unsafe_allow_html=True,
                )

            st.markdown("<hr>", unsafe_allow_html=True)

            # Show/hide game stats based on session state
            if st.session_state.get("show_stats") == game["id"]:
                stats = get_game_stats(game["id"])
                if stats:
                    st.markdown(f"### 📈 Game Stats: {team1['name']} vs {team2['name']}")
                    stat_cols = st.columns(2)
                    for i, (team_name, lines) in enumerate(stats):
                        with stat_cols[i]:
                            st.markdown(f"#### {team_name}")
                            for line in lines:
                                st.markdown(line)

# UI
st.title("📺 Live Sports Scores Dashboard")
st.markdown("Get real-time scores with team logos and click into matchups for full team stats.")

selected_sports = st.sidebar.multiselect(
    "Select sports to display:",
    list(SPORTS.keys()),
    default=list(SPORTS.keys())
)
logo_size = st.sidebar.slider("Team Logo Size", min_value=40, max_value=100, value=60)
refresh_interval = st.sidebar.slider("Auto-refresh every (seconds):", 10, 60, 30)

countdown = st.empty()
for seconds_left in range(refresh_interval, 0, -1):
    countdown.markdown(f"🔄 Refreshing in **{seconds_left}** seconds...")
    time.sleep(1)

# Initialize toggle state
if "show_stats" not in st.session_state:
    st.session_state["show_stats"] = None

# Show scores
for sport in selected_sports:
    display_scores(sport, logo_size)

