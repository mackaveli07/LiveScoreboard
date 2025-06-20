import streamlit as st
import requests
import time
from datetime import datetime, date
from elo import EloRating
import csv

from team_colors_all_leagues import team_colors as TEAM_COLORS
from all_team_logos import team_logos as TEAM_LOGOS
from pathlib import Path
from expandable_game_view import display_game_details

st.set_page_config(page_title="Live Sports Scoreboard", layout="wide")
st.markdown(Path("styles.html").read_text(), unsafe_allow_html=True)

# Auto-refresh session state
REFRESH_INTERVAL = 10  # seconds

# Initialize refresh timer
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()

# Check if it's time to refresh
time_since_last = (datetime.now() - st.session_state.last_refresh).total_seconds()
if time_since_last >= REFRESH_INTERVAL:
    st.session_state.last_refresh = datetime.now()
    st.rerun()

def get_team_colors(team_name):
    colors = TEAM_COLORS.get(team_name)
    if colors:
        return [colors["primary"], colors["secondary"]]
    return ["#333", "#555"]

def get_team_logo(team_name):
    return TEAM_LOGOS.get(team_name, "")

def format_game_team_data(team):
    return {
        "name": team["team"]["displayName"],
        "score": team.get("score", "0"),
        "colors": get_team_colors(team["team"]["displayName"]),
        "logo": get_team_logo(team["team"]["displayName"])
    }

@st.cache_data(ttl=10)
def fetch_espn_scores():
    base_url = "https://site.api.espn.com/apis/site/v2/sports"
    sports = ["baseball/mlb", "football/nfl", "basketball/nba", "basketball/wnba", "hockey/nhl"]
    games = []
    today = date.today().isoformat()
    for sport_path in sports:
        response = requests.get(f"{base_url}/{sport_path}/scoreboard")
        if response.status_code != 200:
            continue
        data = response.json()
        league_slug = sport_path.split("/")[1]
        for event in data.get("events", []):
            if event.get("date", "").split("T")[0] != today:
                continue
            competition = event.get("competitions", [{}])[0]
            competitors = competition.get("competitors", [])
            if len(competitors) < 2:
                continue

            away = next((team for team in competitors if team["homeAway"] == "away"), None)
            home = next((team for team in competitors if team["homeAway"] == "home"), None)
            if not away or not home:
                continue

            status = competition.get("status", {})
            situation = competition.get("situation", {})
            info = {}

            if league_slug == "mlb":
                info = {
                    "inning": status.get("type", {}).get("shortDetail", ""),
                    "at_bat": situation.get("lastPlay", {}).get("athlete", {}).get("displayName", "N/A"),
                    "pitcher": situation.get("pitcher", {}).get("athlete", {}).get("displayName", "N/A"),
                    "onFirst": situation.get("onFirst", False),
                    "onSecond": situation.get("onSecond", False),
                    "onThird": situation.get("onThird", False),
                }
            elif league_slug == "nfl":
                info = {
                    "quarter": f"Q{status.get('period', 'N/A')}",
                    "possession": situation.get("possession", {}).get("displayName", "N/A")
                }
            elif league_slug in ["nba", "wnba"]:
                info = {
                    "quarter": f"Q{status.get('period', 'N/A')}",
                    "clock": status.get("displayClock", "")
                }
            elif league_slug == "nhl":
                info = {
                    "period": f"Period {status.get('period', 'N/A')}",
                    "clock": status.get("displayClock", "")
                }

            games.append({
                "sport": league_slug,
                "away_team": format_game_team_data(away),
                "home_team": format_game_team_data(home),
                "info": info
            })
    return games

def determine_result(home_score, away_score):
    if home_score > away_score:
        return 1
    elif home_score < away_score:
        return 0
    return 0.5

sport_icons = {
    "NBA": "https://a.espncdn.com/i/teamlogos/leagues/500/nba.png",
    "WNBA": "https://a.espncdn.com/i/teamlogos/leagues/500/wnba.png",
    "NFL": "https://a.espncdn.com/i/teamlogos/leagues/500/nfl.png",
    "NHL": "https://a.espncdn.com/i/teamlogos/leagues/500/nhl.png",
    "MLB": "https://a.espncdn.com/i/teamlogos/leagues/500/mlb.png",
}

elo_by_league = {sport: EloRating() for sport in ["mlb", "nba", "wnba", "nfl", "nhl"]}
games = fetch_espn_scores()
available_sports = sorted(set(game.get("sport", "").upper() for game in games))
tabs_keys = available_sports + ["Betting Info", "Elo Ratings"]
tabs = st.tabs(tabs_keys)

for i, tab_key in enumerate(tabs_keys):
    with tabs[i]:
        if tab_key == "Betting Info":
            st.write("Display your betting odds, lines, or other betting info here.")

        elif tab_key == "Elo Ratings":
            for league, elo in elo_by_league.items():
                st.subheader(f"{league.upper()} Elo Ratings")
                for team, rating in elo.get_all_ratings().items():
                    st.write(f"{team}: {round(rating)}")

        else:
            sport = tab_key
            icon_url = sport_icons.get(sport, "")
            st.markdown(f"<h2 style='display:flex; align-items:center; gap:8px;'>"
                        f"<img src='{icon_url}' height='32'/> {sport} Games</h2>", unsafe_allow_html=True)

            filtered_games = [g for g in games if g.get("sport", "").upper() == sport]
            for game in filtered_games:
                away_team, home_team = game["away_team"], game["home_team"]
                info = game.get("info", {})

                col1, col2, col3 = st.columns([3, 2, 3])

                with col1:
                    st.markdown(f"""
                        <div style='background: linear-gradient(135deg, {away_team['colors'][0]}, {away_team['colors'][1]}); border-radius: 10px; padding: 10px;'>
                            <h3>{away_team['name']}</h3>
                            <img src="{away_team['logo']}" width="100" />
                            <p style='font-size: 36px; margin: 10px 0;'>{away_team['score']}</p>
                        </div>""", unsafe_allow_html=True)

                with col2:
                    if sport.lower() == "mlb":
                        first = 'active' if info.get('onFirst') else ''
                        second = 'active' if info.get('onSecond') else ''
                        third = 'active' if info.get('onThird') else ''
                        st.markdown(f"""
                            <div class='info-box'>
                                ⚾ <strong>Inning:</strong> {info.get('inning', '')}<br/>
                                🧂 <strong>At Bat:</strong> {info.get('at_bat', 'N/A')}<br/>
                                🥎 <strong>Pitcher:</strong> {info.get('pitcher', 'N/A')}
                                <div class='diamond'>
                                    <div class='base second {second}'></div>
                                    <div class='base third {third}'></div>
                                    <div class='base first {first}'></div>
                                    <div class='base mound'></div>
                                </div>
                            </div>""", unsafe_allow_html=True)
                    elif sport.lower() in ["nba", "wnba"]:
                        st.markdown(f"**Quarter:** {info.get('quarter', 'N/A')}<br>⏱️ Clock: {info.get('clock', '')}", unsafe_allow_html=True)
                    elif sport.lower() == "nfl":
                        st.markdown(f"**Quarter:** {info.get('quarter', 'N/A')}<br>🟢 Possession: {info.get('possession', '')}", unsafe_allow_html=True)
                    elif sport.lower() == "nhl":
                        st.markdown(f"**Period:** {info.get('period', 'N/A')}<br>⏱️ Clock: {info.get('clock', '')}", unsafe_allow_html=True)

                with col3:
                    try:
                        home_score = int(home_team['score'])
                        away_score = int(away_team['score'])
                        elo = elo_by_league[sport.lower()]
                        result = determine_result(home_score, away_score)
                        elo.update_ratings(home_team["name"], away_team["name"], result)
                        with open("elo_history.csv", "a", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                datetime.now().date(), sport.lower(), home_team["name"], away_team["name"],
                                result, round(elo.get_rating(home_team["name"])), round(elo.get_rating(away_team["name"]))
                            ])
                    except ValueError:
                        pass
                    st.markdown(f"""
                        <div style='background: linear-gradient(135deg, {home_team['colors'][0]}, {home_team['colors'][1]}); border-radius: 10px; padding: 10px;'>
                            <h3>{home_team['name']}</h3>
                            <img src="{home_team['logo']}" width="100" />
                            <p style='font-size: 36px; margin: 10px 0;'>{home_team['score']}</p>
                        </div>""", unsafe_allow_html=True)
