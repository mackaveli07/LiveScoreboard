import streamlit as st
import requests
import time
from datetime import datetime

st.set_page_config(page_title="Live Sports Scores", layout="wide")

# Timer-based manual refresh every 5 seconds without auto rerun on load
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = False

if "schedule_cache" not in st.session_state:
    st.session_state.schedule_cache = {}

# Sidebar controls
col1, col2 = st.sidebar.columns(2)
if col1.button("🔁 Refresh Now"):
    st.session_state.last_refresh = time.time()

if col2.button("⏯ Toggle Auto-Refresh"):
    st.session_state.auto_refresh = not st.session_state.auto_refresh

# Auto refresh logic
if st.session_state.auto_refresh and time.time() - st.session_state.last_refresh > 5:
    st.session_state.last_refresh = time.time()
    st.rerun()

SPORTS = {
    "NFL (Football)": {"path": "football/nfl", "icon": "🏈"},
    "NBA (Basketball)": {"path": "basketball/nba", "icon": "🏀"},
    "MLB (Baseball)": {"path": "baseball/mlb", "icon": "⚾"},
    "NHL (Hockey)": {"path": "hockey/nhl", "icon": "🏒"}
}

TEAM_COLORS = {
    "NE": "#002244", "DAL": "#003594", "GB": "#203731", "KC": "#E31837", "PHI": "#004C54",
    "SF": "#AA0000", "CHI": "#0B162A", "PIT": "#FFB612",
    "LAL": "#552583", "BOS": "#007A33", "GSW": "#1D428A", "MIA": "#98002E", "NYK": "#F58426",
    "NYY": "#003087", "LAD": "#005A9C", "CHC": "#0E3386", "HOU": "#EB6E1F",
    "NYR": "#0038A8", "TOR": "#00205B", "VGK": "#B4975A"
}

game_score_cache = {}

def get_scores(sport_path, date=None):
    cache_key = f"{sport_path}-{date}"
    if cache_key in st.session_state.schedule_cache:
        return st.session_state.schedule_cache[cache_key]

    base_url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard"
    if date:
        base_url += f"?dates={date}"
    try:
        response = requests.get(base_url)
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
        clock = competition['status'].get('displayClock', "")
        possession = competition.get("situation", {}).get("possession")

        inning = competition['status'].get('period', "")
        inning_half = competition['status'].get('half', "") if 'half' in competition['status'] else ""
        inning_display = f"Inning: {inning} ({inning_half.title()})" if inning and inning_half else ""

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
                "id": team_info.get("id", ""),
                "possession": team_info.get("id") == possession
            })

        stats = []
        for comp in competition.get("competitors", []):
            team_info = comp.get("team", {})
            team_name = team_info.get("displayName", "")
            team_logo = team_info.get("logo", "")
            for category in comp.get("statistics", []):
                for stat in category.get("stats", []):
                    if "avg" not in stat.get("name", "").lower():
                        stats.append({
                            "team": team_name,
                            "team_logo": team_logo,
                            "name": stat.get("name", ""),
                            "value": stat.get("displayValue", "")
                        })

        results.append({
            "id": game["id"],
            "status": status,
            "teams": team_data,
            "period": inning_display if "mlb" in sport_path else period,
            "clock": clock,
            "stats": stats
        })

    st.session_state.schedule_cache[cache_key] = results
    return results

def display_scores(sport_name, date):
    sport_config = SPORTS[sport_name]
    scores = get_scores(sport_config["path"], date)
    if not scores:
        return

    st.markdown(f"## {sport_config['icon']} {sport_name}")

    for game in scores:
        team1, team2 = game["teams"]
        status = game["status"]
        period = f"Period: {game['period']}" if game['period'] else ""
        clock = f"Time: {game['clock']}" if game['clock'] else ""
        stats = game.get("stats", [])

        game_id = game['id']
        previous_scores = game_score_cache.get(game_id, (None, None))
        game_score_cache[game_id] = (team1["score"], team2["score"])

        color1 = TEAM_COLORS.get(team1["abbreviation"], "#f0f0f0")
        color2 = TEAM_COLORS.get(team2["abbreviation"], "#f0f0f0")

        with st.container():
            st.markdown("---")
            col1, col2, col3 = st.columns([4, 2, 4])

            with col1:
                st.image(team1["logo"], width=60)
                st.markdown(f"### {team1['name']}")
                st.markdown(f"**Score:** {team1['score']}")
                if team1["possession"]:
                    st.markdown("🏈 Possession")

            with col2:
                st.markdown("### VS")
                st.markdown(f"**Status:** {status}")
                if period:
                    st.markdown(period)
                if clock:
                    st.markdown(clock)

            with col3:
                st.image(team2["logo"], width=60)
                st.markdown(f"### {team2['name']}")
                st.markdown(f"**Score:** {team2['score']}")
                if team2["possession"]:
                    st.markdown("🏈 Possession")

            with st.expander("📊 Show Game Stats"):
                if stats:
                    grouped_stats = {}
                    team_logos = {}
                    for stat in stats:
                        team = stat["team"]
                        if team not in grouped_stats:
                            grouped_stats[team] = []
                            team_logos[team] = stat.get("team_logo", "")
                        grouped_stats[team].append(f"✅ **{stat['name']}**: {stat['value']}")

                    for team, team_stats in grouped_stats.items():
                        with st.container():
                            st.image(team_logos[team], width=40)
                            st.markdown(f"#### 🧢 {team}")
                            for stat_line in team_stats:
                                st.markdown(f"- {stat_line}")
                else:
                    st.markdown("No stats available.")

# UI
st.title("📻 Live Sports Scores Dashboard")
st.markdown("Real-time updates with team logos and stats.")

date_selection = st.sidebar.date_input("Select date (for past games):", datetime.today())
selected_sport = st.sidebar.selectbox("Select a sport:", list(SPORTS.keys()))
formatted_date = date_selection.strftime("%Y%m%d")
display_scores(selected_sport, formatted_date)
