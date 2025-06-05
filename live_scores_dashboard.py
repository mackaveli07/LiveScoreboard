import streamlit as st
import requests

st.set_page_config(page_title="Live Sports Scores", layout="wide")

SPORTS = {
    "NFL (Football)": {"path": "football/nfl"},
    "NBA (Basketball)": {"path": "basketball/nba"},
    "MLB (Baseball)": {"path": "baseball/mlb"},
    "NHL (Hockey)": {"path": "hockey/nhl"}
}

def get_scores(sport_path):
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
        period = competition['status'].get('period', "")
        possession = competition.get("situation", {}).get("possession")

        teams = competition['competitors']
        if len(teams) != 2:
            continue

        team_data = []
        for team in teams:
            team_info = team['team']
            team_data.append({
                "name": team_info.get("displayName", ""),
                "score": team.get("score", "0"),
                "logo": team_info.get("logo", ""),
                "abbreviation": team_info.get("abbreviation", ""),
                "possession": team_info.get("id") == possession
            })

        results.append({
            "id": game["id"],
            "status": status,
            "teams": team_data,
            "period": period
        })

    return results

def display_scores(sport_name, logo_size):
    sport_config = SPORTS[sport_name]
    scores = get_scores(sport_config["path"])
    if not scores:
        return

    st.markdown(f"## 🏆 {sport_name}")

    for game in scores:
        team1, team2 = game["teams"]
        status = game["status"]
        period = f"Period: {game['period']}" if game['period'] else ""

        with st.container():
            st.markdown("---")
            col1, col2, col3 = st.columns([4, 2, 4])

            with col1:
                st.image(team1["logo"], width=logo_size)
                st.markdown(f"### {team1['name']}")
                st.markdown(f"**Score:** {team1['score']}")
                if team1["possession"]:
                    st.markdown("🏈 Possession")

            with col2:
                st.markdown("### VS")
                st.markdown(f"**Status:** {status}")
                st.markdown(f"{period}")

            with col3:
                st.image(team2["logo"], width=logo_size)
                st.markdown(f"### {team2['name']}")
                st.markdown(f"**Score:** {team2['score']}")
                if team2["possession"]:
                    st.markdown("🏈 Possession")

# UI
st.markdown("""
    <style>
        .stApp {
            background-color: #f8f9fa;
            font-family: 'Segoe UI', sans-serif;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📺 Live Sports Scores Dashboard")
st.markdown("Real-time updates with team logos. Sleek modern UI.")

selected_sports = st.sidebar.multiselect(
    "Select sports to display:",
    list(SPORTS.keys()),
    default=list(SPORTS.keys())
)
logo_size = st.sidebar.slider("Team Logo Size", 40, 100, 60)

for sport in selected_sports:
    display_scores(sport, logo_size)
