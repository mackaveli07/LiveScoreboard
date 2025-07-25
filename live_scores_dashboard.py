import streamlit as st
import requests
from datetime import datetime, date
from team_colors_all_leagues import team_colors as TEAM_COLORS
from all_team_logos import team_logos as TEAM_LOGOS
from pathlib import Path
from expandable_game_view import display_game_details

import pandas as pd
import json
from elo_utils import run_elo_pipeline, merge_market_with_elo, save_betting_data
from betiq_scraper import scrape_betiq_odds

# Auto-refresh every 10 seconds
st_autorefresh(interval=10_000, key="refresh")

st.set_page_config(page_title="Live Sports Scoreboard", layout="wide")
st.markdown(Path("styles.html").read_text(), unsafe_allow_html=True)
st.title("🏟️ Live American Sports Scoreboard")
st.caption("🔁 Auto-refreshing every 10 seconds...")

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

@st.cache_data(ttl=5)
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

            info = {}
            status = competition.get("status", {})
            situation = competition.get("situation", {})

            if league_slug == "mlb":
                info = {
                    "inning": status.get("type", {}).get("shortDetail", ""),
                    "at_bat": situation.get("lastPlay", {}).get("athlete", {}).get("displayName", "N/A"),
                    "pitcher": situation.get("pitcher", {}).get("athlete", {}).get("displayName", "N/A"),
                    "onFirst": situation.get("onFirst", False),
                    "onSecond": situation.get("onSecond", False),
                    "onThird": situation.get("onThird", False),
                    "balls": situation.get("balls", 0),
                    "strikes": situation.get("strikes", 0),
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

sport_icons = {
    "NBA": "https://a.espncdn.com/i/teamlogos/leagues/500/nba.png",
    "WNBA": "https://a.espncdn.com/i/teamlogos/leagues/500/wnba.png",
    "NFL": "https://a.espncdn.com/i/teamlogos/leagues/500/nfl.png",
    "NHL": "https://a.espncdn.com/i/teamlogos/leagues/500/nhl.png",
    "MLB": "https://a.espncdn.com/i/teamlogos/leagues/500/mlb.png",
}

games = fetch_espn_scores()

available_sports = sorted(set(game.get("sport", "").upper() for game in games))

tabs_keys = available_sports + ["Betting Info"]
tabs = st.tabs(tabs_keys)

def update_betting_predictions():
    run_elo_pipeline()
    leagues = ["mlb", "nba", "nfl", "nhl", "wnba"]
    for league in leagues:
        market_odds = scrape_betiq_odds(league)
        merged = merge_market_with_elo(league, market_odds)
        save_betting_data(league, merged)
        with open(f"{league}_predicted_odds.json", "w") as f:
            json.dump(merged, f, indent=2)

for i, tab_key in enumerate(tabs_keys):
    with tabs[i]:
        if tab_key == "Betting Info":
            st.header("📈 Elo Predictions vs BetIQ Market")
            if st.button("🔁 Refresh Elo Ratings + Odds"):
                update_betting_predictions()
                st.success("Betting predictions updated!")
            leagues = ["mlb", "nba", "nfl", "nhl", "wnba"]
            betting_tabs = st.tabs([l.upper() for l in leagues])
            for j, league in enumerate(leagues):
                with betting_tabs[j]:
                    try:
                        with open(f"{league}_predicted_odds.json", "r") as f:
                            data = json.load(f)
                        df = pd.DataFrame(data)
                        df["Value On"] = df.apply(lambda x: "HOME" if x["value_edge_home"] > x["value_edge_away"] else "AWAY", axis=1)
                        st.dataframe(df, use_container_width=True)
                    except Exception as e:
                        st.warning(f"Could not load betting data for {league.upper()}: {e}")
        else:
            sport = tab_key
            icon_url = sport_icons.get(sport, "")
            st.markdown(f"<h2 style='display:flex; align-items:center; gap:8px;'><img src='{icon_url}' height='32'/> {sport} Games</h2>", unsafe_allow_html=True)
            filtered_games = [game for game in games if game.get("sport", "").upper() == sport]
            for game in filtered_games:
                away_team = game["away_team"]
                home_team = game["home_team"]
                info = game.get("info", {})
                col1, col2, col3 = st.columns([3, 2, 3])
                with col1:
                    st.markdown(f"""
                        <div style='background: linear-gradient(135deg, {away_team['colors'][0]}, {away_team['colors'][1]}); border-radius: 10px; padding: 10px;'>
                            <h3>{away_team['name']}</h3>
                            <img src="{away_team['logo']}" width="100" />
                            <p style='font-size: 36px; margin: 10px 0;'>{away_team['score']}</p>
                        </div>
                    """, unsafe_allow_html=True)
                with col2:
                    sport_lower = sport.lower()
                    if sport_lower == "mlb":
                        first = 'active' if info.get('onFirst') else ''
                        second = 'active' if info.get('onSecond') else ''
                        third = 'active' if info.get('onThird') else ''
                        at_bat = info.get('at_bat', 'N/A')
                        pitcher = info.get('pitcher', 'N/A')
                        balls = info.get('balls', 0)
                        strikes = info.get('strikes', 0)
                        st.markdown(f"""
                            <div class='info-box'>
                                ⚾ <strong>Inning:</strong> {info.get('inning', '')}<br/>
                                🧢 <strong>At Bat:</strong> {at_bat}<br/>
                                🥎 <strong>Pitcher:</strong> {pitcher}<br/>
                                🎯 <strong>Count:</strong> {balls} Balls, {strikes} Strikes
                                <div class='diamond'>
                                    <div class='base second {second}'></div>
                                    <div class='base third {third}'></div>
                                    <div class='base first {first}'></div>
                                    <div class='base mound'></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    elif sport_lower in ["nba", "wnba"]:
                        st.markdown(f"""
                            <div class='info-box'>
                                🏀 <strong>Quarter:</strong> {info.get('quarter', 'N/A')}<br/>
                                ⏱️ <strong>Clock:</strong> {info.get('clock', '')}
                                <div class='court responsive-court'>
                                    <div class='half-court'></div>
                                    <div class='top-hoop'></div>
                                    <div class='bottom-hoop'></div>
                                    <div class='top-ft-arc'></div>
                                    <div class='bottom-ft-arc'></div>
                                    <div class='top-3pt-arc'></div>
                                    <div class='bottom-3pt-arc'></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    elif sport_lower == "nfl":
                        st.markdown(f"**Quarter:** {info.get('quarter', 'N/A')}<br>🟢 Possession: {info.get('possession', '')}", unsafe_allow_html=True)
                    elif sport_lower == "nhl":
                        st.markdown(f"**Period:** {info.get('period', 'N/A')}<br>⏱️ Clock: {info.get('clock', '')}", unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""
                        <div style='background: linear-gradient(135deg, {home_team['colors'][0]}, {home_team['colors'][1]}); border-radius: 10px; padding: 10px;'>
                            <h3>{home_team['name']}</h3>
                            <img src="{home_team['logo']}" width="100" />
                            <p style='font-size: 36px; margin: 10px 0;'>{home_team['score']}</p>
                        </div>
                    """, unsafe_allow_html=True)
