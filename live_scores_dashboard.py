import streamlit as st
import requests

st.set_page_config(page_title="Live Sports Scores", layout="wide")

SPORTS = {
    "NFL (Football)": {"path": "football/nfl"},
    "NBA (Basketball)": {"path": "basketball/nba"},
    "MLB (Baseball)": {"path": "baseball/mlb"},
    "NHL (Hockey)": {"path": "hockey/nhl"}
}

TEAM_COLORS = {
    "NFL": {
        "New England Patriots": "#002244",
        "Green Bay Packers": "#203731",
        "Dallas Cowboys": "#041E42",
        "Philadelphia Eagles": "#004C54",
    },
    "NBA": {
        "Miami Heat": "#98002E",
        "Golden State Warriors": "#1D428A",
        "Los Angeles Lakers": "#552583",
        "Boston Celtics": "#007A33",
    },
    "MLB": {
        "Boston Red Sox": "#BD3039",
        "New York Yankees": "#132448",
        "Chicago Cubs": "#0E3386",
        "Los Angeles Dodgers": "#005A9C",
    },
    "NHL": {
        "Chicago Blackhawks": "#CF0A2C",
        "Boston Bruins": "#FFB81C",
        "Toronto Maple Leafs": "#00205B",
        "Montreal Canadiens": "#AF1E2D",
    }
}

st.markdown("""
    <style>
    .stat-card {
        background: #ffffff;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        margin: 8px 0;
        padding: 12px 16px;
        display: flex;
        align-items: center;
        animation: fadeIn 0.5s ease-in-out;
        transition: all 0.3s ease;
    }
    .stat-card:hover {
        background: #f0f4f8;
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }
    .stat-logo {
        width: 32px;
        height: 32px;
        object-fit: contain;
        margin-right: 12px;
        border-radius: 4px;
        background: #eee;
        padding: 2px;
    }
    .stat-text {
        flex-grow: 1;
    }
    .stat-name {
        font-weight: 600;
        color: #222;
        font-size: 15px;
    }
    .stat-value {
        font-weight: bold;
        color: #1f77b4;
        font-size: 15px;
    }
    @keyframes fadeIn {
        0% { opacity: 0; transform: translateY(5px); }
        100% { opacity: 1; transform: translateY(0); }
    }
    </style>
""", unsafe_allow_html=True)

# Cache for scores
game_score_cache = {}

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

        stats = competition.get("statistics", [])

        results.append({
            "id": game["id"],
            "status": status,
            "teams": team_data,
            "period": inning_display if "mlb" in sport_path else period,
            "clock": clock,
            "stats": stats
        })

    return results

def display_scores(sport_name):
    sport_config = SPORTS[sport_name]
    scores = get_scores(sport_config["path"])
    if not scores:
        return

    st.markdown(f"## 🏆 {sport_name}")

    for game in scores:
        team1, team2 = game["teams"]
        status = game["status"]
        period = f"<span style='font-weight:bold;color:#1f77b4;'>Period:</span> {game['period']}" if game['period'] else ""
        clock = f"<span style='font-weight:bold;color:#d62728;'>Time:</span> {game['clock']}" if game['clock'] else ""
        stats = game.get("stats", [])

        game_id = game['id']
        previous_scores = game_score_cache.get(game_id, (None, None))
        game_score_cache[game_id] = (team1["score"], team2["score"])

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
                    st.markdown(period, unsafe_allow_html=True)
                if clock:
                    st.markdown(clock, unsafe_allow_html=True)

            with col3:
                st.image(team2["logo"], width=60)
                st.markdown(f"### {team2['name']}")
                st.markdown(f"**Score:** {team2['score']}")
                if team2["possession"]:
                    st.markdown("🏈 Possession")

            with st.expander("📊 Show Game Stats"):
                if stats:
                    team_stats = {}
                    for stat in stats:
                        team = stat.get("team", "Unknown Team")
                        if team not in team_stats:
                            team_stats[team] = []
                        team_stats[team].append(stat)

                    for team_name, stat_list in team_stats.items():
                        logo = next((t['logo'] for t in game["teams"] if t['name'] == team_name), "")
                        league = sport_name.split(" ")[0]
                        team_color = TEAM_COLORS.get(league, {}).get(team_name, "#1f77b4")

                        with st.expander(f"🟢 {team_name} Stats"):
                            for stat in stat_list:
                                st.markdown(
                                    f"""
                                    <div class=\"stat-card\" style=\"border-left: 5px solid {team_color};\">
                                        <img src=\"{logo}\" class=\"stat-logo\" />
                                        <div class=\"stat-text\">
                                            <div class=\"stat-name\">{stat['name']}</div>
                                        </div>
                                        <div class=\"stat-value\">{stat['value']}</div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )
                else:
                    st.markdown("No stats available.")

# UI
st.title("📻 Live Sports Scores Dashboard")
st.markdown("Real-time updates with team logos and stats.")

selected_sports = st.sidebar.multiselect(
    "Select sports to display:",
    list(SPORTS.keys()),
    default=list(SPORTS.keys())
)

if st.sidebar.button("🔁 Refresh Scores"):
    st.experimental_rerun()

for sport in selected_sports:
    display_scores(sport)
