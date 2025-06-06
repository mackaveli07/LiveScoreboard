import streamlit as st
import requests
from streamlit_extras.st_autorefresh import st_autorefresh

st.set_page_config(page_title="Live Sports Scores", layout="wide")

# ⏱️ Optional Auto-Refresh Toggle
auto_refresh = st.sidebar.checkbox("Auto-Refresh Every 5s", value=True)
if auto_refresh:
    st_autorefresh(interval=5000, limit=None, key="auto_refresh_toggle")
else:
    if st.sidebar.button("🔄 Manual Refresh"):
        st.experimental_rerun()

# 💅 Custom CSS for subtle animation
st.markdown("""
    <style>
    .score {
        font-size: 2rem;
        font-weight: 800;
        color: #1f77b4;
        transition: all 0.4s ease-in-out;
    }

    .score-change {
        animation: pop 0.5s ease;
        color: #28a745;
    }

    @keyframes pop {
        0% { transform: scale(1); opacity: 0.6; }
        50% { transform: scale(1.3); opacity: 1; }
        100% { transform: scale(1); opacity: 1; }
    }
    </style>
""", unsafe_allow_html=True)

# 🎯 Supported Sports
SPORTS = {
    "NFL (Football)": {"path": "football/nfl"},
    "NBA (Basketball)": {"path": "basketball/nba"},
    "MLB (Baseball)": {"path": "baseball/mlb"},
    "NHL (Hockey)": {"path": "hockey/nhl"}
}

# 🧠 Score cache for change detection
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

        # MLB: inning and half
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

def display_scores(sport_name, logo_size):
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
        team1_changed = previous_scores[0] != team1["score"]
        team2_changed = previous_scores[1] != team2["score"]
        game_score_cache[game_id] = (team1["score"], team2["score"])

        with st.container():
            st.markdown("---")
            col1, col2, col3 = st.columns([4, 2, 4])

            with col1:
                st.image(team1["logo"], width=logo_size)
                st.markdown(f"### {team1['name']}")
                score_class_1 = "score score-change" if team1_changed else "score"
                st.markdown(f"<div class='{score_class_1}'>{team1['score']}</div>", unsafe_allow_html=True)
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
                st.image(team2["logo"], width=logo_size)
                st.markdown(f"### {team2['name']}")
                score_class_2 = "score score-change" if team2_changed else "score"
                st.markdown(f"<div class='{score_class_2}'>{team2['score']}</div>", unsafe_allow_html=True)
                if team2["possession"]:
                    st.markdown("🏈 Possession")

            with st.expander("Show Game Stats"):
                if stats:
                    for stat in stats:
                        st.markdown(f"- {stat.get('name', '')}: {stat.get('displayValue', '')}")
                else:
                    st.markdown("No stats available.")

# 🎨 UI Layout
st.title("📻 Live Sports Scores Dashboard")
st.markdown("Real-time updates with team logos, clean animations, and sleek UI.")

selected_sports = st.sidebar.multiselect(
    "Select sports to display:",
    list(SPORTS.keys()),
    default=list(SPORTS.keys())
)
logo_size = st.sidebar.slider("Team Logo Size", 40, 100, 60)

for sport in selected_sports:
    display_scores(sport, logo_size)
