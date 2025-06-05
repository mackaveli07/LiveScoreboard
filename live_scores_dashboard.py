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
        period = competition['status']['period']
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
        team_name = team.get("team", {}).get("displayName", "Unknown")
        lines = []
        for cat in team.get("statistics", []):
            label = cat.get("label", "Stat")
            stat = cat.get("stats", ["-"])[0]
            lines.append(f"{label}: {stat}")
        stats.append((team_name, lines))
    return stats

def display_scores(sport_name, logo_size):
    sport_path = SPORTS[sport_name]["path"]
    scores = get_scores(sport_path)
    if not scores:
        return

    st.subheader(sport_name)

    for game in scores:
        team1, team2 = game["teams"]
        status = game["status"]
        possession1 = " (🏈)" if team1["possession"] else ""
        possession2 = " (🏈)" if team2["possession"] else ""

        with st.expander(f"{team1['name']} vs {team2['name']} - {status}"):
            col1, col2, col3 = st.columns([4, 2, 4])

            with col1:
                st.image(team1["logo"], width=logo_size)
                st.write(team1["name"] + possession1)
                st.write("Score:", team1["score"])

            with col2:
                st.markdown("**VS**")
                st.text(f"Status: {status}")
                st.text(f"Period: {game['period']}")
                if st.toggle("View Stats", key=f"stats_{game['id']}"):
                    stats = get_game_stats(game["id"], sport_path)
                    if stats:
                        stat_cols = st.columns(2)
                        for i, (team_name, lines) in enumerate(stats):
                            with stat_cols[i]:
                                st.write(team_name)
                                for line in lines:
                                    st.text(line)

            with col3:
                st.image(team2["logo"], width=logo_size)
                st.write(team2["name"] + possession2)
                st.write("Score:", team2["score"])

# UI
st.title("Live Sports Scores Dashboard")

selected_sports = st.sidebar.multiselect(
    "Select sports to display:",
    list(SPORTS.keys()),
    default=list(SPORTS.keys())
)
logo_size = st.sidebar.slider("Team Logo Size", 40, 100, 60)

for sport in selected_sports:
    display_scores(sport, logo_size)
