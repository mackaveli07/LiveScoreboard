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
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from html import escape

# ============================================================================
# CONSTANTS & CONFIG
# ============================================================================

REFRESH_INTERVAL = 10  # seconds
FETCH_TIMEOUT = 10  # seconds
ESPN_BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"

SPORTS_CONFIG = {
    "baseball/mlb": {
        "league": "mlb",
        "name": "MLB",
        "icon": "https://a.espncdn.com/i/teamlogos/leagues/500/mlb.png",
    },
    "football/nfl": {
        "league": "nfl",
        "name": "NFL",
        "icon": "https://a.espncdn.com/i/teamlogos/leagues/500/nfl.png",
    },
    "basketball/nba": {
        "league": "nba",
        "name": "NBA",
        "icon": "https://a.espncdn.com/i/teamlogos/leagues/500/nba.png",
    },
    "basketball/wnba": {
        "league": "wnba",
        "name": "WNBA",
        "icon": "https://a.espncdn.com/i/teamlogos/leagues/500/wnba.png",
    },
    "hockey/nhl": {
        "league": "nhl",
        "name": "NHL",
        "icon": "https://a.espncdn.com/i/teamlogos/leagues/500/nhl.png",
    },
}

BETTING_LEAGUES = ["mlb", "nba", "nfl", "nhl", "wnba"]

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class TeamData:
    name: str
    score: str
    colors: List[str]
    logo: str

@dataclass
class GameInfo:
    sport: str
    league: str
    away_team: TeamData
    home_team: TeamData
    info: Dict[str, Any]

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def safe_get(obj: Any, *keys, default: Any = None) -> Any:
    """Safely navigate nested dictionaries."""
    for key in keys:
        if isinstance(obj, dict):
            obj = obj.get(key)
            if obj is None:
                return default
        else:
            return default
    return obj if obj is not None else default

def get_team_colors(team_name: str) -> List[str]:
    """Get team colors with fallback to defaults."""
    colors = TEAM_COLORS.get(team_name, {})
    return [colors.get("primary", "#333"), colors.get("secondary", "#555")]

def get_team_logo(team_name: str) -> str:
    """Get team logo URL."""
    return TEAM_LOGOS.get(team_name, "")

def format_team_data(team: Optional[Dict]) -> TeamData:
    """Convert API team data to TeamData object."""
    if not team or "team" not in team:
        return TeamData(name="TBD", score="0", colors=["#333", "#555"], logo="")
    
    display_name = safe_get(team, "team", "displayName", default="Unknown")
    return TeamData(
        name=display_name,
        score=str(safe_get(team, "score", default="0")),
        colors=get_team_colors(display_name),
        logo=get_team_logo(display_name),
    )

# ============================================================================
# SESSION STATE MANAGEMENT
# ============================================================================

def init_session_state():
    """Initialize session state variables."""
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = time.time()
    if "updating_bets" not in st.session_state:
        st.session_state.updating_bets = False

def should_refresh() -> bool:
    """Check if auto-refresh should trigger."""
    if st.session_state.get("updating_bets", False):
        return False
    return time.time() - st.session_state.last_refresh > REFRESH_INTERVAL

def trigger_refresh():
    """Trigger page refresh."""
    st.session_state.last_refresh = time.time()
    st.rerun()

init_session_state()
if should_refresh():
    trigger_refresh()

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(page_title="Live Sports Scoreboard", layout="wide")
try:
    st.markdown(Path("styles.html").read_text(), unsafe_allow_html=True)
except FileNotFoundError:
    pass

st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at top, #f8fbff 0%, #f2f5fb 40%, #eef2f8 100%);
    }
    .dashboard-header {
        background: rgba(255, 255, 255, 0.75);
        border: 1px solid #e4e9f2;
        border-radius: 14px;
        box-shadow: 0 6px 20px rgba(17, 24, 39, 0.08);
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .section-header {
        display: flex;
        align-items: center;
        gap: 10px;
        background: #ffffff;
        border: 1px solid #e7ebf3;
        border-radius: 12px;
        box-shadow: 0 3px 12px rgba(17, 24, 39, 0.06);
        padding: 10px 14px;
        margin: 8px 0 14px;
    }
    .section-header h3 {
        margin: 0;
        color: #1f2a44;
        font-weight: 700;
    }
    .score-tile {
        background: #ffffff;
        border: 1px solid #e6ebf3;
        border-radius: 16px;
        box-shadow: 0 8px 22px rgba(15, 23, 42, 0.07);
        padding: 16px 18px;
        margin-bottom: 14px;
    }
    .tile-head {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        margin-bottom: 6px;
    }
    .league-badge {
        background: #edf3ff;
        border: 1px solid #d7e3ff;
        color: #1d4ed8;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: .6px;
        border-radius: 999px;
        padding: 3px 10px;
    }
    .team-card {
        text-align: center;
        padding: 10px 8px;
    }
    .team-name {
        font-size: 16px;
        font-weight: 700;
        line-height: 1.25;
        color: #172034;
        margin-top: 6px;
    }
    .team-score {
        font-size: 34px;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: .5px;
        margin-top: 2px;
    }
    .info-panel {
        background: #f8faff;
        border: 1px solid #e3e9f5;
        border-radius: 12px;
        padding: 10px 12px;
        text-align: center;
        color: #263145;
        font-size: 13px;
        line-height: 1.55;
    }
    .info-title {
        color: #4b5567;
        font-weight: 600;
        font-size: 11px;
        letter-spacing: .4px;
        text-transform: uppercase;
    }
    .betting-shell {
        background: #ffffff;
        border: 1px solid #e5ebf5;
        border-radius: 14px;
        box-shadow: 0 6px 20px rgba(15, 23, 42, 0.06);
        padding: 10px 12px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #e5eaf3;
        padding-bottom: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background: #f5f7fb;
        border: 1px solid #e5eaf3;
        border-radius: 9px 9px 0 0;
        padding: 8px 14px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background: #ffffff;
        color: #0f172a;
        border-color: #d9e3f4;
    }
    .stButton button {
        border-radius: 8px;
        border: 1px solid #cfdaf0;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class='dashboard-header'>
        <h1 style='margin: 0; color: #10182b;'>🏟️ Live American Sports Scoreboard</h1>
        <p style='margin: 6px 0 0; color: #4a5568;'>🔁 Auto-refreshing every 10 seconds...</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ============================================================================
# GAME DATA FETCHING
# ============================================================================

@st.cache_data(ttl=5)
def fetch_espn_scores() -> List[GameInfo]:
    """Fetch live game scores from ESPN API."""
    games = []
    today = date.today().isoformat()
    
    for sport_path, config in SPORTS_CONFIG.items():
        try:
            response = requests.get(
                f"{ESPN_BASE_URL}/{sport_path}/scoreboard",
                timeout=FETCH_TIMEOUT,
            )
            if response.status_code != 200:
                continue
            
            data = response.json()
            league = config["league"]
            events = data.get("events", []) if isinstance(data, dict) else []
            
            for event in events:
                if not isinstance(event, dict):
                    continue
                    
                if not event.get("date", "").startswith(today):
                    continue
                
                competitions = event.get("competitions", [])
                if not competitions or not isinstance(competitions, list):
                    continue
                
                competition = competitions[0]
                if not isinstance(competition, dict):
                    continue
                    
                competitors = competition.get("competitors", [])
                
                if len(competitors) < 2:
                    continue
                
                away = next(
                    (t for t in competitors if isinstance(t, dict) and t.get("homeAway") == "away"), None
                )
                home = next(
                    (t for t in competitors if isinstance(t, dict) and t.get("homeAway") == "home"), None
                )
                
                if not away or not home:
                    continue
                
                try:
                    game_info = extract_game_info(league, competition)
                    
                    games.append(
                        GameInfo(
                            sport=config["name"],
                            league=league,
                            away_team=format_team_data(away),
                            home_team=format_team_data(home),
                            info=game_info,
                        )
                    )
                except Exception as e:
                    continue
        
        except requests.RequestException as e:
            st.warning(f"Failed to fetch {config['name']}: {str(e)[:100]}")
        except Exception as e:
            st.warning(f"Error parsing {config['name']} data: {str(e)[:100]}")
    
    return games

def extract_game_info(league: str, competition: Dict) -> Dict[str, Any]:
    """Extract league-specific game info from competition data."""
    if not isinstance(competition, dict):
        return {}
    
    status = competition.get("status", {})
    situation = competition.get("situation", {})
    
    # Ensure status and situation are dicts
    if not isinstance(status, dict):
        status = {}
    if not isinstance(situation, dict):
        situation = {}
    
    info = {}
    
    try:
        if league == "mlb":
            status_type = status.get("type", {})
            last_play = situation.get("lastPlay", {})
            pitcher = situation.get("pitcher", {})
            
            # Safely get nested values
            inning = ""
            if isinstance(status_type, dict):
                inning = status_type.get("shortDetail", "")
            
            at_bat = "N/A"
            if isinstance(last_play, dict) and last_play.get("athlete"):
                at_bat = last_play["athlete"].get("displayName", "N/A")
            
            pitcher_name = "N/A"
            if isinstance(pitcher, dict) and pitcher.get("athlete"):
                pitcher_name = pitcher["athlete"].get("displayName", "N/A")
            
            info = {
                "inning": inning,
                "at_bat": at_bat,
                "pitcher": pitcher_name,
                "onFirst": bool(situation.get("onFirst")),
                "onSecond": bool(situation.get("onSecond")),
                "onThird": bool(situation.get("onThird")),
                "balls": situation.get("balls", 0),
                "strikes": situation.get("strikes", 0),
            }
        
        elif league == "nfl":
            possession = situation.get("possession", {})
            possession_abbr = "N/A"
            if isinstance(possession, dict):
                possession_abbr = possession.get("abbreviation", "N/A")
            
            # Get field position (yard line)
            field_position = safe_get(situation, "lastPlay", "statistics", 0, "yards", default="")
            yard_line = safe_get(situation, "yardLine", default="")
            down_distance = safe_get(situation, "shortDownDistanceText", default="")
            
            # Get last play description
            last_play_text = safe_get(situation, "lastPlay", "text", default="")
            
            info = {
                "quarter": f"Q{status.get('period', 'N/A')}",
                "possession": possession_abbr,
                "yard_line": yard_line,
                "down_distance": down_distance,
                "last_play": last_play_text,
            }
        
        elif league in ["nba", "wnba"]:
            info = {
                "quarter": f"Q{status.get('period', 'N/A')}",
                "clock": status.get("displayClock", ""),
            }
        
        elif league == "nhl":
            info = {
                "period": f"Period {status.get('period', 'N/A')}",
                "clock": status.get("displayClock", ""),
            }
    
    except Exception:
        # Return empty info dict if anything goes wrong
        info = {}
    
    return info

# ============================================================================
# BETTING DATA
# ============================================================================

@st.cache_data(ttl=300)
def load_betting_data(league: str) -> List[Dict]:
    """Load cached betting predictions."""
    try:
        with open(f"{league}_predicted_odds.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def update_betting_predictions():
    """Update all league betting predictions."""
    st.session_state.updating_bets = True
    try:
        run_elo_pipeline()
        for league in BETTING_LEAGUES:
            try:
                market_odds = scrape_betiq_odds(league)
                merged = merge_market_with_elo(league, market_odds)
                save_betting_data(league, merged)
                with open(f"{league}_predicted_odds.json", "w") as f:
                    json.dump(merged, f, indent=2)
            except Exception as e:
                st.warning(f"Error updating {league.upper()}: {str(e)[:100]}")
    except Exception as e:
        st.error(f"Error in betting pipeline: {str(e)[:100]}")
    finally:
        st.session_state.updating_bets = False

# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_team_card(team: TeamData, align: str = "right") -> str:
    """Render a team score card."""
    team_name = escape(team.name)
    team_score = escape(team.score)
    logo_html = (
        f"<img src='{escape(team.logo)}' width='56' style='display: block; margin: 0 auto;' alt='{team_name} logo'><br>"
        if team.logo
        else ""
    )
    return f"""
    <div class='team-card' style='text-align: {align};'>
        {logo_html}
        <div class='team-name'>{team_name}</div>
        <div class='team-score'>{team_score}</div>
    </div>
    """

def render_mlb_info(info: Dict) -> str:
    """Render MLB-specific game info."""
    first = "●" if info.get("onFirst") else "○"
    second = "●" if info.get("onSecond") else "○"
    third = "●" if info.get("onThird") else "○"
    
    first_color = "green" if info.get("onFirst") else "gray"
    second_color = "green" if info.get("onSecond") else "gray"
    third_color = "green" if info.get("onThird") else "gray"
    
    return f"""
    <div class='info-panel'>
        <div class='info-title'>MLB Live Situation</div>
        ⚾ Inning: {escape(str(info.get('inning', '')))}<br>
        🧢 At Bat: {escape(str(info.get('at_bat', 'N/A')))}<br>
        🥎 Pitcher: {escape(str(info.get('pitcher', 'N/A')))}<br>
        🎯 Count: {escape(str(info.get('balls', 0)))} Balls, {escape(str(info.get('strikes', 0)))} Strikes<br><br>
        <table style='margin: 0 auto; border-collapse: collapse;'>
            <tr>
                <td style='width: 40px; text-align: center;'></td>
                <td style='width: 40px; text-align: center; color: {second_color}; font-size: 20px;'>{second}</td>
                <td style='width: 40px; text-align: center;'></td>
            </tr>
            <tr>
                <td style='width: 40px; text-align: center; color: {third_color}; font-size: 20px;'>{third}</td>
                <td style='width: 40px; text-align: center;'></td>
                <td style='width: 40px; text-align: center; color: {first_color}; font-size: 20px;'>{first}</td>
            </tr>
            <tr>
                <td style='width: 40px; text-align: center;'></td>
                <td style='width: 40px; text-align: center; font-weight: bold;'>H</td>
                <td style='width: 40px; text-align: center;'></td>
            </tr>
        </table>
    </div>
    """

def render_field_position(yard_line: str) -> str:
    """Render a visual field position indicator."""
    if not yard_line:
        return "<div style='text-align: center; color: #6b7280;'>No field position data</div>"
    
    # Parse yard line (e.g., "50", "20" means 20 yards from endzone)
    try:
        yards = int(yard_line.replace("+", ""))
        # Calculate percentage position on field (0 = away endzone, 100 = home endzone)
        position_percent = yards * 2  # Scale 0-50 to 0-100
    except Exception:
        position_percent = 50
    
    # Create field visualization
    return f"""
    <div style='text-align: center; margin: 10px 0;'>
        <div style='font-size: 12px; font-weight: bold; margin-bottom: 5px;'>{yard_line} Yard Line</div>
        <div style='background: linear-gradient(to right, #1a4d2e 0%, #2d5a3d 40%, #ffffff 50%, #2d5a3d 60%, #1a4d2e 100%); height: 30px; position: relative; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);'>
            <div style='position: absolute; top: 50%; left: {position_percent}%; transform: translate(-50%, -50%); width: 8px; height: 8px; background: #FF6B6B; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.5);'></div>
        </div>
        <div style='font-size: 10px; color: #5f6674; margin-top: 4px;'>Away ← Field Position → Home</div>
    </div>
    """

def render_last_play(last_play_text: str) -> str:
    """Render the last play description with styling."""
    if not last_play_text:
        return "<div style='text-align: center; color: #6b7280; font-size: 12px;'>No play data available</div>"
    
    # Truncate if too long
    display_text = escape(last_play_text[:150] + "..." if len(last_play_text) > 150 else last_play_text)
    
    return f"""
    <div style='background: #f7f9fd; border-left: 4px solid #FF6B6B; padding: 10px; border-radius: 6px; margin-top: 8px;'>
        <div style='font-size: 11px; color: #5f6674; margin-bottom: 4px;'>📋 LAST PLAY</div>
        <div style='font-size: 12px; color: #333; line-height: 1.4;'>{display_text}</div>
    </div>
    """

def render_nfl_info(info: Dict) -> str:
    """Render NFL-specific game info with field position and last play."""
    yard_line = info.get("yard_line", "")
    down_distance = info.get("down_distance", "")
    possession = info.get("possession", "N/A")
    quarter = info.get("quarter", "N/A")
    last_play = info.get("last_play", "")
    
    field_viz = render_field_position(yard_line)
    last_play_viz = render_last_play(last_play)
    down_info = f"<br>📊 {escape(down_distance)}" if down_distance else ""
    
    return f"""
    <div class='info-panel'>
        <div class='info-title'>NFL Game Flow</div>
        🏈 {escape(quarter)}<br>
        🟢 Possession: {escape(possession)}{down_info}
        {field_viz}
        {last_play_viz}
    </div>
    """

def render_nba_wnba_info(info: Dict) -> str:
    """Render NBA/WNBA game info."""
    return f"""
    <div class='info-panel'>
        <div class='info-title'>Live Game Clock</div>
        🏀 Quarter: {escape(str(info.get('quarter', 'N/A')))}<br>
        ⏱️ Clock: {escape(str(info.get('clock', '')))}
    </div>
    """

def render_nhl_info(info: Dict) -> str:
    """Render NHL game info."""
    return f"""
    <div class='info-panel'>
        <div class='info-title'>Live Game Clock</div>
        🏒 {escape(str(info.get('period', 'N/A')))}<br>
        ⏱️ Clock: {escape(str(info.get('clock', '')))}
    </div>
    """

def get_info_renderer(league: str):
    """Get the appropriate info renderer for a league."""
    renderers = {
        "mlb": render_mlb_info,
        "nba": render_nba_wnba_info,
        "wnba": render_nba_wnba_info,
        "nfl": render_nfl_info,
        "nhl": render_nhl_info,
    }
    return renderers.get(league, lambda x: "")

def render_game_card(game: GameInfo):
    """Render a single game card."""
    st.markdown(
        f"<div class='tile-head'><span class='league-badge'>{escape(game.league.upper())}</span></div>",
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([3, 2, 3])
    
    with col1:
        st.markdown(render_team_card(game.away_team, align="right"), unsafe_allow_html=True)
    
    with col2:
        renderer = get_info_renderer(game.league)
        st.markdown(renderer(game.info), unsafe_allow_html=True)
    
    with col3:
        st.markdown(render_team_card(game.home_team, align="left"), unsafe_allow_html=True)

# ============================================================================
# BETTING TAB
# ============================================================================

def render_betting_tab():
    """Render the betting information tab."""
    st.markdown(
        "<div class='section-header'><h3>📈 Elo Predictions vs BetIQ Market</h3></div>",
        unsafe_allow_html=True,
    )
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔁 Refresh", key="refresh_bets"):
            update_betting_predictions()
            st.success("Predictions updated!")
    
    betting_tabs = st.tabs([l.upper() for l in BETTING_LEAGUES])
    
    for league_tab, league in zip(betting_tabs, BETTING_LEAGUES):
        with league_tab:
            try:
                data = load_betting_data(league)
                if data:
                    df = pd.DataFrame(data)
                    df["Value On"] = df.apply(
                        lambda x: "HOME"
                        if x.get("value_edge_home", 0) > x.get("value_edge_away", 0)
                        else "AWAY",
                        axis=1,
                    )
                    preferred_order = [
                        "away_team",
                        "home_team",
                        "elo_home_pct",
                        "market_home_odds",
                        "value_edge_home",
                        "value_edge_away",
                        "Value On",
                    ]
                    available_cols = [col for col in preferred_order if col in df.columns]
                    remaining_cols = [col for col in df.columns if col not in available_cols]
                    display_df = df[available_cols + remaining_cols]
                    st.markdown("<div class='betting-shell'>", unsafe_allow_html=True)
                    formatters = {
                        "elo_home_pct": "{:.1f}%",
                        "market_home_odds": "{:.2f}",
                        "value_edge_home": "{:.2f}",
                        "value_edge_away": "{:.2f}",
                    }
                    active_formatters = {
                        key: value for key, value in formatters.items() if key in display_df.columns
                    }
                    styled_df = display_df.style.format(active_formatters) if active_formatters else display_df
                    st.dataframe(styled_df, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.info(f"No betting data for {league.upper()} yet.")
            except Exception as e:
                st.warning(f"Could not load {league.upper()} data: {str(e)[:100]}")

# ============================================================================
# SCORES TAB
# ============================================================================

def render_scores_tabs(games: List[GameInfo]):
    """Render tabs for each sport."""
    available_sports = sorted(set(game.sport for game in games))
    
    if not available_sports:
        st.info("No live games currently.")
        return
    
    tabs_keys = available_sports + ["Betting Info"]
    tabs = st.tabs(tabs_keys)
    
    # Sport tabs
    for tab, sport in zip(tabs[:-1], available_sports):
        with tab:
            config = next(
                (c for c in SPORTS_CONFIG.values() if c["name"] == sport), None
            )
            if config:
                st.markdown(
                    f"<div class='section-header'>"
                    f"<img src='{escape(config['icon'])}' width='30' style='vertical-align:middle;'> "
                    f"<h3>{escape(sport)} Games</h3></div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f"### {sport} Games")
            
            sport_games = [g for g in games if g.sport == sport]
            
            if not sport_games:
                st.write("No live games currently.")
                continue
            
            for game in sport_games:
                render_game_card(game)
                st.divider()
    
    # Betting tab
    with tabs[-1]:
        render_betting_tab()

# ============================================================================
# MAIN
# ============================================================================

try:
    games = fetch_espn_scores()
except Exception as e:
    st.error(f"Failed to fetch live scores: {str(e)[:100]}")
    games = []

render_scores_tabs(games)
