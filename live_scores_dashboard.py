import streamlit as st
import requests
import st_autorefresh  # ✅ Updated import

st.set_page_config(page_title="Live Sports Scores", layout="wide")

SPORTS = {
    "NFL (Football)": "football/nfl",
    "NBA (Basketball)": "basketball/nba",
    "MLB (Baseball)": "baseball/mlb",
    "NHL (Hockey)": "hockey/nhl"
}

def sanitize_hex(color):
    return f"#{color}" if color and len(color) == 6 else "#000000"

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
            continue  # Skip malformed games

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

def set_background_color():
    st.markdown("""
        <style>
        .stApp {
            background-color: #e28743;
        }
        </style>
    """, unsafe_allow_html=True)

set_background_color()

def display_scores(sport_name, logo_size):
    st.subheader(f"🏆 {sport_name}")
    scores = get_scores_with_colors(SPORTS[sport_name])
    if not scores:
        st.info("No live or recent games currently.")
        return

    for game in scores:
        team1, team2 = game["teams"]
        with st.expander(f"{team1['name']} vs {team2['name']} - {game['status']}"):
            col1, col2, col3 = st.columns([4, 2, 4])

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
                toggle_key = f"show_stats_{game['id']}"
                show = st.toggle("📊 View Stats", key=toggle_key)

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

# ✅ Auto-refresh logic using streamlit-extras
st_autorefresh(interval=refresh_interval * 1000, key="auto_refresh")

# Display selected sports
for sport in selected_sports:
    display_scores(sport, logo_size)
