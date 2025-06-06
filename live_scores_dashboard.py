import streamlit as st
import requests

st.set_page_config(page_title="Live Sports Scores", layout="wide")

SPORTS = {
    "NFL (Football)": {"path": "football/nfl"},
    "NBA (Basketball)": {"path": "basketball/nba"},
    "MLB (Baseball)": {"path": "baseball/mlb"},
    "NHL (Hockey)": {"path": "hockey/nhl"}
}

# Cache using session_state
if "game_score_cache" not in st.session_state:
    st.session_state.game_score_cache = {}

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
        competition = game.get('competitions', [{}])[0]
        status = competition.get('status', {}).get('type', {}).get('shortDetail', "")
        period = competition.get('status', {}).get('period', "")
        clock = competition.get('status', {}).get('displayClock', "")
        possession = competition.get("situation", {}).get("possession")

        # MLB specific: inning and top/bottom
        inning = competition.get('status', {}).get('period', "")
        inning_half = competition.get('status', {}).get('half', "")
        inning_display = ""
        if inning:
            if isinstance(inning_half, str) and inning_half:
                inning_display = f"Inning: {inning} ({inning_half.title()})"
            else:
                inning_display = f"Inning: {inning}"

        teams = competition.get('competitors', [])
        if len(teams) != 2:
            continue

        team_data = []
        for team in teams:
            team_info = team.get('team', {})
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
            "id": game.get("id", ""),
            "status": status,
            "teams": team_data,
            "period": inning_display if "mlb" in sport_path else str(period),
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
    game_score_cache = st.session_state.game_score_cache

    for game in scores:
        team1, team2 = game["teams"]
        status = game["status"]
        period = game.get("period", "")
        clock = game.get("clock", "")
        stats = game.get("stats", [])

        # Format HTML safely
        period_display = f"<span style='font-weight:bold;color:#1f77b4;'>Period:</span> {period}" if period else ""
        clock_display = f"<span style='font-weight:bold;color:#d62728;'>Time:</span> {clock}" if clock else ""

        # Detect score changes
        game_id = game.get("id", "")
        previous_scores = game_score_cache.get(game_id, (None, None))
        team1_changed = previous_scores[0] != team1.get("score", "0")
        team2_changed = previous_scores[1] != team2.get("score", "0")
        game_score_cache[game_id] = (team1.get("score", "0"), team2.get("score", "0"))

        with st.container():
            st.markdown("---")
            col1, col2, col3 = st.columns([4, 2, 4])

            with col1:
                if team1["logo"]:
                    st.image(team1["logo"], width=logo_size)
                st.markdown(f"### {team1['name']}")
                if team1_changed:
                    st.markdown(
                        f"<span style='color:green; font-weight:bold;'>Score: {team1.get('score', '0')} ⬆</span>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(f"**Score:** {team1.get('score', '0')}")
                if team1.get("possession"):
                    st.markdown("🏈 Possession")

            with col2:
                st.markdown("### VS")
                st.markdown(f"**Status:** {status}")
                if period_display:
                    st.markdown(period_display, unsafe_allow_html=True)
                if clock_display:
                    st.markdown(clock_display, unsafe_allow_html=True)

            with col3:
                if team2["logo"]:
                    st.image(team2["logo"], width=logo_size)
                st.markdown(f"### {team2['name']}")
                if team2_changed:
                    st.markdown(
                        f"<span style='color:green; font-weight:bold;'>Score: {team2.get('score', '0')} ⬆</span>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(f"**Score:** {team2.get('score', '0')}")
                if team2.get("possession"):
                    st.markdown("🏈 Possession")

            with st.expander("Show Game Stats"):
                if stats:
                    for stat in stats:
                        st.markdown(f"- {stat.get('name', '')}: {stat.get('displayValue', '')}")
                else:
                    st.markdown("No stats available.")

# UI
st.title("📻 Live Sports Scores Dashboard")
st.markdown("Real-time updates with team logos. Sleek modern UI.")

selected_sports = st.sidebar.multiselect(
    "Select sports to display:",
    list(SPORTS.keys()),
    default=list(SPORTS.keys())
)
logo_size = st.sidebar.slider("Team Logo Size", 40, 100, 60)

if st.sidebar.button("Refresh Scores"):
    st.experimental_rerun()

for sport in selected_sports:
    display_scores(sport, logo_size)
