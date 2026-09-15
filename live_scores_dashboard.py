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
import time

# Define constants
REFRESH_INTERVAL = 10  # seconds

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

# Only refresh if NOT updating betting data
if not st.session_state.get("updating_bets", False):
    if time.time() - st.session_state.last_refresh > REFRESH_INTERVAL:
        st.session_state.last_refresh = time.time()
        st.rerun()

st.set_page_config(page_title="Live Sports Scoreboard", layout="wide")
try:
    st.markdown(Path("styles.html").read_text(), unsafe_allow_html=True)
except FileNotFoundError:
    pass  # Ignore if styles.html doesn't exist

st.title("🏟️ Live American Sports Scoreboard")
st.caption("🔁 Auto-refreshing every 10 seconds...")

def get_team_colors(team_name):
    colors = TEAM_COLORS.get(team_name, {})
    primary = colors.get("primary", "#333")
    secondary = colors.get("secondary", "#555")
    return [primary, secondary]

def get_team_logo(team_name):
    return TEAM_LOGOS.get(team_name, "")

def format_game_team_data(team):
    if not team or "team" not in team:
        return {
            "name": "TBD",
            "score": "0",
            "colors": ["#333", "#555"],
            "logo": ""
        }
    return {
        "name": team["team"].get("displayName", "Unknown"),
        "score": str(team.get("score", "0")),
        "colors": get_team_colors(team["team"]["displayName"]),
        "logo": get_team_logo(team["team"]["displayName"])
    }

def update_betting_predictions():
    st.session_state.updating_bets = True
    try:
        run_elo_pipeline()
        leagues = ["mlb", "nba", "nfl", "nhl", "wnba"]
        for league in leagues:
            market_odds = scrape_betiq_odds(league)
            merged = merge_market_with_elo(league, market_odds)
            save_betting_data(league, merged)
            with open(f"{league}_predicted_odds.json", "w") as f:
                json.dump(merged, f, indent=2)
    except Exception as e:
        st.error(f"Error updating betting predictions: {e}")
    finally:
        st.session_state.updating_bets = False

@st.cache_data(ttl=5)
def fetch_espn_scores():
    base_url = "https://site.api.espn.com/apis/site/v2/sports"
    sports = ["baseball/mlb", "football/nfl", "basketball/nba", "basketball/wnba", "hockey/nhl"]
    games = []
    today = date.today().isoformat()
    
    for sport_path in sports:
        try:
            response = requests.get(f"{base_url}/{sport_path}/scoreboard", timeout=10)
            if response.status_code != 200:
                continue
            data = response.json()
            league_slug = sport_path.split("/")[-1]
            events = data.get("events", [])
            
            for event in events:
                if not event.get("date", "").startswith(today):
                    continue
                competitions = event.get("competitions", [])
                if len(competitions) == 0:
                    continue
                competition = competitions[0]
                competitors = competition.get("competitors", [])
                if len(competitors) < 2:
                    continue

                away = next((team for team in competitors if team.get("homeAway") == "away"), None)
                home = next((team for team in competitors if team.get("homeAway") == "home"), None)

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
                        "onFirst": bool(situation.get("onFirst")),
                        "onSecond": bool(situation.get("onSecond")),
                        "onThird": bool(situation.get("onThird")),
                        "balls": situation.get("balls", 0),
                        "strikes": situation.get("strikes", 0),
                    }
                elif league_slug == "nfl":
                    info = {
                        "quarter": f"Q{status.get('period', 'N/A')}",
                        "possession": situation.get("possession", {}).get("abbreviation", "N/A")
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
        except Exception as e:
            continue  # Skip this sport if there's an error
    
    return games

@st.cache_data(ttl=300)
def load_betting_data(league):
    """Placeholder function - actual implementation may vary"""
    try:
        with open(f"{league}_predicted_odds.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Fetch games
try:
    games = fetch_espn_scores()
except Exception as e:
    st.error("Failed to fetch live scores. Please try again later.")
    games = []

# Get available sports from games
available_sports = sorted(set(game.get("sport", "").upper() for game in games if game.get("sport")))

# Create tabs
tabs_keys = available_sports + ["Betting Info"]
tabs = st.tabs(tabs_keys)

# Betting Info Tab
with tabs[-1]:
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
                if not df.empty:
                    df["Value On"] = df.apply(
                        lambda x: "HOME" if x.get("value_edge_home", 0) > x.get("value_edge_away", 0) else "AWAY", 
                        axis=1
                    )
                st.dataframe(df, use_container_width=True)
            except FileNotFoundError:
                st.info(f"No betting data available for {league.upper()} yet. Click 'Refresh' to generate.")
            except Exception as e:
                st.warning(f"Could not load betting data for {league.upper()}: {e}")

# Sport-specific tabs
sport_icons = {
    "NBA": "https://a.espncdn.com/i/teamlogos/leagues/500/nba.png",
    "WNBA": "https://a.espncdn.com/i/teamlogos/leagues/500/wnba.png",
    "NFL": "https://a.espncdn.com/i/teamlogos/leagues/500/nfl.png",
    "NHL": "https://a.espncdn.com/i/teamlogos/leagues/500/nhl.png",
    "MLB": "https://a.espncdn.com/i/teamlogos/leagues/500/mlb.png",
}

for i, tab_key in enumerate(tabs_keys[:-1]):  # Exclude last tab (Betting Info)
    with tabs[i]:
        sport = tab_key
        icon_url = sport_icons.get(sport, "")
        if icon_url:
            st.markdown(f"<img src='{icon_url}' width='30' style='vertical-align:middle;'> <h3 style='display:inline;'>{sport} Games</h3>", unsafe_allow_html=True)
        else:
            st.markdown(f"### {sport} Games")
            
        filtered_games = [game for game in games if game.get("sport", "").upper() == sport]
        
        if not filtered_games:
            st.write("No live games currently.")
            continue
            
        for game in filtered_games:
            away_team = game["away_team"]
            home_team = game["home_team"]
            info = game.get("info", {})
            col1, col2, col3 = st.columns([3, 2, 3])
            
            with col1:
                st.markdown(f"""
                    <div style='text-align: right; padding: 10px;'>
                        <div style='font-size: 18px; font-weight: bold;'>{away_team['name']}</div>
                        <div style='font-size: 24px; font-weight: bold; color: #000;'>{away_team['score']}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with col2:
                sport_lower = game["sport"]
                if sport_lower == "mlb":
                    first = '●' if info.get('onFirst') else '○'
                    second = '●' if info.get('onSecond') else '○'
                    third = '●' if info.get('onThird') else '○'
                    at_bat = info.get('at_bat', 'N/A')
                    pitcher = info.get('pitcher', 'N/A')
                    balls = info.get('balls', 0)
                    strikes = info.get('strikes', 0)
                    st.markdown(f"""
                        <div style='text-align: center; font-family: monospace;'>
                            ⚾ Inning: {info.get('inning', '')}<br>
                            🧢 At Bat: {at_bat}<br>
                            🥎 Pitcher: {pitcher}<br>
                            🎯 Count: {balls} Balls, {strikes} Strikes<br><br>
                            <div style='line-height: 1.8; letter-spacing: 2px;'>
                                <div style='color: {'green' if info.get('onSecond') else 'gray'}'>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{second}</div>
                                <div style='color: {'green' if info.get('onThird') else 'gray'}'>{third}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{first}</div>
                                <div>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;H</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                
                elif sport_lower in ["nba", "wnba"]:
                    st.markdown(f"""
                        <div style='text-align: center;'>
                            🏀 Quarter: {info.get('quarter', 'N/A')}<br>
                            ⏱️ Clock: {info.get('clock', '')}
                        </div>
                    """, unsafe_allow_html=True)
                
                elif sport_lower == "nfl":
                    possession = info.get('possession', '')
                    st.markdown(f"""
                        <div style='text-align: center;'>
                            Quarter: {info.get('quarter', 'N/A')}<br>
                            🟢 Possession: {possession if possession else 'N/A'}
                        </div>
                    """, unsafe_allow_html=True)
                
                elif sport_lower == "nhl":
                    st.markdown(f"""
                        <div style='text-align: center;'>
                            Period: {info.get('period', 'N/A')}<br>
                            ⏱️ Clock: {info.get('clock', '')}
                        </div>
                    """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                    <div style='text-align: left; padding: 10px;'>
                        <div style='font-size: 18px; font-weight: bold;'>{home_team['name']}</div>
                        <div style='font-size: 24px; font-weight: bold; color: #000;'>{home_team['score']}</div>
                    </div>
                """, unsafe_allow_html=True)
