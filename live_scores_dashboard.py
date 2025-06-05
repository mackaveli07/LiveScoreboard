import streamlit as st
import requests

# League-specific themes
league_themes = {
    "NFL (Football)": {"bg": "#013369", "text": "#ffffff"},
    "NBA (Basketball)": {"bg": "#1D428A", "text": "#ffffff"},
    "MLB (Baseball)": {"bg": "#002D72", "text": "#ffffff"},
    "NHL (Hockey)": {"bg": "#111111", "text": "#ffffff"},
}

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
            continue

        possession = next((t["team"]["abbreviation"] for t in teams if t.get("possession")), "")
        period = competition.get("status", {}).get("period", "")
        clock = competition.get("status", {}).get("displayClock", "")

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
                "logo": team_info['logo'],
                "color": colors,
                "alt_color": alt_color,
                "abbreviation": team_info['abbreviation'],
                "has_possession": team.get("possession", False)
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

def apply_league_theme(sport_name):
    theme = league_themes.get(sport_name, {"bg": "#ffffff", "text": "#000000"})
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: {theme['bg']};
            color: {theme['text']};
        }}
        </style>
    """, unsafe_allow_html=True)

def show_top_ticker(selected_sports):
    ticker_html = '<div style="display: flex; overflow-x: auto; padding: 10px; background: #333;">'
    for sport in selected_sports:
        games = get_scores_with_colors(SPORTS[sport])
        for game in games:
            t1, t2 = game["teams"]
            ticker_html += f"""
                <div style="display: flex; align-items: center; margin-right: 20px; color: white;">
                    <img src="{t1['logo']}" height="24" style="margin-right: 4px;" />
                    <strong>{t1['abbreviation']}</strong> {t1['score']} - {t2['score']} <strong>{t2['abbreviation']}</strong>
                    <img src="{t2['logo']}" height="24" style="margin-left: 4px;" />
                </div>
            """
    ticker_html += '</div>'
    st.markdown(ticker_html, unsafe_allow_html=True)

def display_scores(sport_name):
    apply_league_theme(sport_name)
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
                st.image(team1["logo"], width=60)
                st.markdown(f"<div style='font-size: 20px; color:{team1['color']}'>{team1['name']}</div>", unsafe_allow_html=True)
                style = "border: 3px solid yellow;" if team1["has_possession"] else ""
                st.markdown(f"<div style='{style} background-color:{team1['color']}; color:{team1['alt_color']}; padding:6px 12px; font-size:24px; border-radius:8px;'>{team1['score']}</div>", unsafe_allow_html=True)

            with col2:
                st.markdown("<div style='text-align:center; font-size: 16px;'>VS</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:center; font-size: 14px;'>Status:<br><strong>{game['status']}</strong></div>", unsafe_allow_html=True)
                st.markdown(f"<div style='text-align:center; font-size: 13px;'>Q/P: {game['period']}<br>Clock: {game['clock']}</div>", unsafe_allow_html=True)
                toggle_key = f"show_stats_{game['id']}"
                show = st.toggle("📊 View Stats", key=toggle_key)

            with col3:
                st.image(team2["logo"], width=60)
                st.markdown(f"<div style='font-size: 20px; color:{team2['color']}'>{team2['name']}</div>", unsafe_allow_html=True)
                style = "border: 3px solid yellow;" if team2["has_possession"] else ""
                st.markdown(f"<div style='{style} background-color:{team2['color']}; color:{team2['alt_color']}; padding:6px 12px; font-size:24px; border-radius:8px;'>{team2['score']}</div>", unsafe_allow_html=True)

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
st.set_page_config(page_title="Live Sports Scores", layout="wide")
st.title("📺 Live Sports Scores Dashboard")
st.markdown("Real-time scores with team logos, ticker bar, and stats on click.")

selected_sports = st.sidebar.multiselect(
    "Select sports to display:",
    list(SPORTS.keys()),
    default=list(SPORTS.keys())
)

# Top ticker bar
show_top_ticker(selected_sports)

# Show each sport section
for sport in selected_sports:
    display_scores(sport)
