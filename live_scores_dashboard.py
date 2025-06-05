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
    response = requests.get(url)
    data = response.json()
    games = data.get("events", [])

    results = []
    for game in games:
        competition = game['competitions'][0]
        status = competition['status']['type']['shortDetail']
        teams = competition['competitors']

        game_data = {
            "status": status,
            "teams": []
        }

        for team in teams:
            team_info = team['team']
            colors = team_info.get("color", "000000")
            alt_color = team_info.get("alternateColor", "FFFFFF")
            game_data["teams"].append({
                "name": team_info['displayName'],
                "score": team.get('score', '0'),
                "logo": team_info['logo'],
                "color": f"#{colors}",
                "alt_color": f"#{alt_color}"
            })

        results.append(game_data)
    return results

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

st.title("📺 Live Sports Scores Dashboard")
st.markdown("Get real-time scores with team logos and colors for major leagues.")

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

st.experimental_rerun()

for sport in selected_sports:
    display_scores(sport, logo_size)
