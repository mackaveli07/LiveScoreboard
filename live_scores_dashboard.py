import streamlit as st
import requests

st.set_page_config(page_title="Live Sports Scores", layout="wide")

SPORTS = {
    "NFL (Football)": "football/nfl",
    "NBA (Basketball)": "basketball/nba",
    "MLB (Baseball)": "baseball/mlb",
    "NHL (Hockey)": "hockey/nhl"
}

LEAGUE_THEMES = {
    "NFL (Football)": "#013369",
    "NBA (Basketball)": "#1D428A",
    "MLB (Baseball)": "#002D72",
    "NHL (Hockey)": "#111111",
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
        possession = competition.get("situation", {}).get("possession", "")
        period = competition.get("status", {}).get("period", "")
        clock = competition.get("status", {}).get("displayClock", "")
        teams = competition['competitors']

        if len(teams) != 2:
            continue  # Skip malformed games

        game_data = {
            "status": status,
            "teams": [],
            "id": game["id"],
            "possession": possession,
            "period": period,
            "clock": clock
        }

        for team in teams:
            team_info = team['team']
            colors = sanitize_hex(team_info.get("color"))
            alt_color = sanitize_hex(team_info.get("alternateColor"))
            game_data["teams"].append({
                "name": team_info['displayName'],
                "score": team.get('score', '0'),
                "logo": team_info.get('logo', ''),
                "color": colors,
                "alt_color": alt_color,
                "abbreviation": team_info.get('abbreviation', ''),
                "id": team_info.get("id", ""),
                "has_possession": team_info.get("id") == possession
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

def display_scores(sport_name, logo_size):
    theme_color = LEAGUE_THEMES.get(sport_name, "#444")
    scores = get_scores_with_colors(SPORTS[sport_name])
    if not scores:
        st.info("No live or recent games currently.")
        return

    # 🔵 Ticker Bar
    st.markdown(f"<div style='background-color:{theme_color}; padding: 10px;'>", unsafe_allow_html=True)
    ticker_text = ""
    for game in scores:
        if len(game.get("teams", [])) != 2:
            continue

        team1, team2 = game["teams"]
        required_fields = ["name", "score", "logo", "color", "alt_color", "abbreviation"]
        if not all(field in team1 for field in required_fields) or not all(field in team2 for field in required_fields):
            continue

        ticker_text += f"""
            <span style='color:white; margin-right:30px;'>
                <img src="{team1['logo']}" height="20" style="vertical-align:middle;">
                {team1['abbreviation']} <strong>{team1['score']}</strong>
                -
                <strong>{team2['score']}</strong> {team2['abbreviation']}
                <img src="{team2['logo']}" height="20" style="vertical-align:middle;">
                ({game['status']})
            </span>
        """
    st.markdown(f"<marquee scrollamount='5'>{ticker_text}</marquee></div>", unsafe_allow_html=True)

    # 🔵 Game Cards
    for game in scores:
        if len(game.get("teams", [])) != 2:
            continue
        team1, team2 = game["teams"]
        required_fields = ["name", "score", "logo", "color", "alt_color", "abbreviation"]
        if not all(field in team1 for field in required_fields) or not all(field in team2 for field in required_fields):
            st.warning(f"⚠️ Skipping game due to missing data: {team1.get('name', 'Unknown')} vs {team2.get('name', 'Unknown')}")
            continue

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
                if team1["has_possession"]:
                    st.markdown("🏈 Possession", unsafe_allow_html=True)

            with col2:
                st.markdown("<div style='text-align:center; font-size: 16px; color: gray;'>VS</div>", unsafe_allow_html=True)
                st.markdown(
                    f"<div style='text-align:center; font-size: 14px; color: #666;'>Status:<br><strong>{game['status']}</strong><br>Period: {game['period']}<br>Clock: {game['clock']}</div>",
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
                if team2["has_possession"]:
                    st.markdown("🏈 Possession", unsafe_allow_html=True)

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
st.markdown("Real-time scores with logos, possession, and stats for NFL, NBA, MLB, NHL games.")

selected_sports = st.sidebar.multiselect(
    "Select sports to display:",
    list(SPORTS.keys()),
    default=list(SPORTS.keys())
)
logo_size = st.sidebar.slider("Team Logo Size", min_value=40, max_value=100, value=60)

# Render sports
for sport in selected_sports:
    display_scores(sport, logo_size)
