import streamlit as st
import requests

st.set_page_config(page_title="Live Sports Scores", layout="wide")

SPORTS = {
    "NFL (Football)": {"path": "football/nfl", "theme_color": "#013369"},
    "NBA (Basketball)": {"path": "basketball/nba", "theme_color": "#C9082A"},
    "MLB (Baseball)": {"path": "baseball/mlb", "theme_color": "#0C2340"},
    "NHL (Hockey)": {"path": "hockey/nhl", "theme_color": "#111111"}
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
        period = competition['status']['period']
        possession = competition['situation'].get("possession") if competition.get("situation") else None

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
                "color": sanitize_hex(team_info.get("color")),
                "alt_color": sanitize_hex(team_info.get("alternateColor")),
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
            lines.append(f"**{label}**: {stat}")
        stats.append((team_name, lines))
    return stats

def render_ticker(games, league_color):
    if not games:
        return

    ticker_html = f"""
    <div style='background-color:{league_color}; padding:10px; overflow:hidden; white-space:nowrap;'>
    """
    for game in games:
        team1, team2 = game['teams']
        ticker_html += f"""
        <span style='margin-right:30px; color:white; font-weight:bold; display:inline-block;'>
            <img src="{team1['logo']}" width="20" style="vertical-align:middle;"> {team1['abbreviation']} {team1['score']} 
            vs 
            {team2['abbreviation']} {team2['score']} <img src="{team2['logo']}" width="20" style="vertical-align:middle;">
            ({game['status']})
        </span>
        """
    ticker_html += "</div>"

    st.markdown(ticker_html, unsafe_allow_html=True)

def display_scores(sport_name, logo_size):
    sport_config = SPORTS[sport_name]
    scores = get_scores_with_colors(sport_config["path"])
    if not scores:
        return

    render_ticker(scores, sport_config["theme_color"])
    st.subheader(f"🏆 {sport_name}")

    for game in scores:
        team1, team2 = game["teams"]
        status = game["status"]
        period = f"Period: {game['period']}"

        with st.expander(f"{team1['name']} vs {team2['name']} - {status}"):
            col1, col2, col3 = st.columns([4, 2, 4])

            with col1:
                st.image(team1["logo"], width=logo_size)
                st.markdown(f"<div style='color:{team1['color']}; font-weight:bold;'>{team1['name']}</div>", unsafe_allow_html=True)
                st.markdown(
                    f"<div style='background-color:{team1['color']}; color:{team1['alt_color']}; padding:6px 12px; display:inline-block; font-size:24px; border-radius:8px;'>{team1['score']}</div>",
                    unsafe_allow_html=True
                )
                if team1["possession"]:
                    st.markdown("🏈 Possession")

            with col2:
                st.markdown(f"<div style='text-align:center; color:gray;'>VS</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:center; font-size:14px;'>Status:<br><strong>{status}</strong></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:center;'>{period}</div>", unsafe_allow_html=True)
                if st.toggle("📊 View Stats", key=f"show_stats_{game['id']}"):
                    stats = get_game_stats(game["id"], sport_config["path"])
                    if stats:
                        stat_cols = st.columns(2)
                        for i, (team_name, lines) in enumerate(stats):
                            with stat_cols[i]:
                                st.markdown(f"#### {team_name}")
                                for line in lines:
                                    st.markdown(line)

            with col3:
                st.image(team2["logo"], width=logo_size)
                st.markdown(f"<div style='color:{team2['color']}; font-weight:bold;'>{team2['name']}</div>", unsafe_allow_html=True)
                st.markdown(
                    f"<div style='background-color:{team2['color']}; color:{team2['alt_color']}; padding:6px 12px; display:inline-block; font-size:24px; border-radius:8px;'>{team2['score']}</div>",
                    unsafe_allow_html=True
                )
                if team2["possession"]:
                    st.markdown("🏈 Possession")

# UI
st.title("📺 Live Sports Scores Dashboard")
st.markdown("Real-time updates with team logos, colors, stats, and league themes.")

selected_sports = st.sidebar.multiselect(
    "Select sports to display:",
    list(SPORTS.keys()),
    default=list(SPORTS.keys())
)
logo_size = st.sidebar.slider("Team Logo Size", 40, 100, 60)

for sport in selected_sports:
    display_scores(sport, logo_size)
