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
import re
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
BETTING_DISPLAY_COLUMNS = [
    "away",
    "home",
    "prob_home",
    "market_ml_away",
    "market_ml_home",
    "spread",
    "total",
    "value_edge_home",
    "value_edge_away",
]

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


def normalize_team_name(team_name: str) -> str:
    """Normalize team names for cross-source matching."""
    return re.sub(r"[^a-z0-9]+", " ", str(team_name).lower()).strip()


def build_team_aliases(team_name: str) -> set[str]:
    """Build a small alias set for matching sportsbook and ESPN names."""
    normalized = normalize_team_name(team_name)
    aliases = {normalized}
    tokens = normalized.split()

    for size in (1, 2, 3):
        if len(tokens) >= size:
            aliases.add(" ".join(tokens[-size:]))

    return {alias for alias in aliases if alias}


@st.cache_data(ttl=300)
def load_betiq_odds(league: str, refresh_key: int = 0) -> List[Dict[str, Any]]:
    """Load live BetIQ odds for a league."""
    try:
        return scrape_betiq_odds(league)
    except Exception:
        return []


def find_game_odds(
    league: str, away_team: str, home_team: str, refresh_key: int = 0
) -> Optional[Dict[str, Any]]:
    """Find BetIQ odds for the given game."""
    away_aliases = build_team_aliases(away_team)
    home_aliases = build_team_aliases(home_team)

    for odds in load_betiq_odds(league, refresh_key=refresh_key):
        if (
            normalize_team_name(odds.get("away", "")) in away_aliases
            and normalize_team_name(odds.get("home", "")) in home_aliases
        ):
            return odds

    return None


def format_moneyline(value: Any) -> str:
    """Format moneyline values for display."""
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return "N/A"
    return f"+{numeric}" if numeric > 0 else str(numeric)

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
    .league-badge {
        background: #edf3ff;
        border: 1px solid #d7e3ff;
        color: #1d4ed8;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: .6px;
        text-transform: uppercase;
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
    .team-odds {
        margin-top: 8px;
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        background: rgba(15, 23, 42, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.28);
    }
    .team-odds-label {
        font-size: 9px;
        color: rgba(255, 255, 255, 0.82);
        text-transform: uppercase;
        letter-spacing: .45px;
        font-weight: 700;
    }
    .team-odds-value {
        font-size: 13px;
        color: #ffffff;
        font-weight: 800;
        margin-top: 1px;
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
    .odds-panel {
        margin-top: 10px;
        background: #ffffff;
    }
    .info-title {
        color: #4b5567;
        font-weight: 600;
        font-size: 11px;
        letter-spacing: .4px;
        text-transform: uppercase;
    }
    .odds-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 8px;
        margin-top: 8px;
    }
    .odds-chip {
        background: #eef4ff;
        border: 1px solid #d8e3fb;
        border-radius: 10px;
        padding: 8px 10px;
    }
    .odds-chip-label {
        font-size: 10px;
        color: #5f6674;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .35px;
    }
    .odds-chip-value {
        font-size: 14px;
        font-weight: 700;
        color: #172034;
        margin-top: 2px;
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
    .stTabs [data-baseweb="tab"]:focus-visible,
    .stTabs [data-baseweb="tab"]:focus {
        outline: 2px solid #2563eb !important;
        outline-offset: 2px !important;
    }
    .stButton button {
        border-radius: 8px;
        border: 1px solid #cfdaf0;
        font-weight: 600;
    }
    .stButton button:focus-visible,
    .stButton button:focus {
        outline: 2px solid #2563eb !important;
        outline-offset: 2px !important;
    }
    .mlb-diamond-wrap {
        display: inline-block;
        padding: 12px 16px;
        border-radius: 10px;
        background: linear-gradient(135deg, #1b5e20, #2e7d32);
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    .mlb-diamond-table {
        margin: 0 auto;
        border-collapse: collapse;
    }
    .mlb-diamond-table td {
        width: 40px;
        text-align: center;
    }
    .mlb-base {
        font-size: 24px;
        line-height: 1;
    }
    .mlb-home {
        color: white;
        font-weight: bold;
    }
    .mlb-occupied {
        color: #00C853;
    }
    .mlb-empty {
        color: #F5F5F5;
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
def fetch_espn_league_scores(sport_path: str, refresh_key: int = 0) -> List[GameInfo]:
    """Fetch live game scores for a single league from ESPN API."""
    config = SPORTS_CONFIG.get(sport_path)
    if not config:
        return []

    games = []
    today = date.today().isoformat()

    try:
        response = requests.get(
            f"{ESPN_BASE_URL}/{sport_path}/scoreboard",
            timeout=FETCH_TIMEOUT,
        )
        if response.status_code != 200:
            return []

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
            except Exception:
                continue

    except requests.RequestException as e:
        st.warning(f"Failed to fetch {config['name']}: {str(e)[:100]}")
    except Exception as e:
        st.warning(f"Error parsing {config['name']} data: {str(e)[:100]}")

    return games


@st.cache_data(ttl=5)
def fetch_espn_scores() -> List[GameInfo]:
    """Fetch live game scores from ESPN API."""
    games = []
    for sport_path in SPORTS_CONFIG:
        games.extend(fetch_espn_league_scores(sport_path))
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
def load_betting_data(league: str, refresh_key: int = 0) -> List[Dict]:
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


def build_betting_display_df(
    data: List[Dict[str, Any]], recommendation_col: str = "Value On"
) -> pd.DataFrame:
    """Build a formatted betting dataframe for display."""
    df = pd.DataFrame(data)
    if df.empty:
        return df

    df[recommendation_col] = df.apply(
        lambda row: (
            "HOME"
            if row.get("value_edge_home", 0) > row.get("value_edge_away", 0)
            else (
                "AWAY"
                if row.get("value_edge_away", 0) > row.get("value_edge_home", 0)
                else "PASS"
            )
        ),
        axis=1,
    )
    preferred_order = BETTING_DISPLAY_COLUMNS + [recommendation_col]
    available_cols = [col for col in preferred_order if col in df.columns]
    remaining_cols = [col for col in df.columns if col not in available_cols]
    return df[available_cols + remaining_cols].copy()


def get_betting_column_config(columns) -> Dict[str, Any]:
    """Build column configuration for betting data tables."""
    column_config = {}
    if "prob_home" in columns:
        column_config["prob_home"] = st.column_config.NumberColumn(
            "Elo Home %", format="%.3f"
        )
    if "market_ml_home" in columns:
        column_config["market_ml_home"] = st.column_config.NumberColumn(
            "BetIQ Home ML", format="%d"
        )
    if "market_ml_away" in columns:
        column_config["market_ml_away"] = st.column_config.NumberColumn(
            "BetIQ Away ML", format="%d"
        )
    if "spread" in columns:
        column_config["spread"] = st.column_config.NumberColumn(
            "Spread", format="%.1f"
        )
    if "total" in columns:
        column_config["total"] = st.column_config.NumberColumn(
            "Total", format="%.1f"
        )
    if "value_edge_home" in columns:
        column_config["value_edge_home"] = st.column_config.NumberColumn(
            "Value Edge Home", format="%.2f"
        )
    if "value_edge_away" in columns:
        column_config["value_edge_away"] = st.column_config.NumberColumn(
            "Value Edge Away", format="%.2f"
        )
    return column_config


def render_betting_table(
    league: str,
    empty_message: str,
    recommendation_col: str = "Value On",
    refresh_key: int = 0,
):
    """Render a betting table for a given league."""
    data = load_betting_data(league, refresh_key=refresh_key)
    if not data:
        st.info(empty_message)
        return

    display_df = build_betting_display_df(data, recommendation_col=recommendation_col)
    column_config = get_betting_column_config(display_df.columns)
    st.dataframe(
        display_df,
        use_container_width=True,
        column_config=column_config if column_config else None,
    )

# ============================================================================
# UI COMPONENTS
# ============================================================================

def render_team_card(team: TeamData, align: str = "right", moneyline: Any = None) -> str:
    """Render a team score card."""
    team_name = escape(team.name)
    team_score = escape(team.score)
    primary = team.colors[0] if isinstance(team.colors, list) and len(team.colors) > 0 else "#1f2937"
    secondary = team.colors[1] if isinstance(team.colors, list) and len(team.colors) > 1 else "#111827"
    gradient = f"linear-gradient(140deg, {escape(str(primary))} 0%, {escape(str(secondary))} 100%)"
    logo_html = (
        f"<img src='{escape(team.logo)}' width='56' style='display: block; margin: 0 auto;' alt='{team_name} logo'><br>"
        if team.logo
        else ""
    )
    moneyline_display = format_moneyline(moneyline) if moneyline is not None else "N/A"
    odds_html = (
        f"""
        <div class='team-odds'>
            <div class='team-odds-label'>Moneyline</div>
            <div class='team-odds-value'>{escape(moneyline_display)}</div>
        </div>
        """
        if moneyline_display != "N/A"
        else ""
    )
    return f"""
    <div class='team-card' style='text-align: {align}; background: {gradient}; border: 1px solid rgba(255,255,255,0.24); border-radius: 12px; box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06);'>
        {logo_html}
        <div class='team-name' style='color: #ffffff;'>{team_name}</div>
        <div class='team-score' style='color: #ffffff; text-shadow: 0 1px 3px rgba(0,0,0,0.35);'>{team_score}</div>
        {odds_html}
    </div>
    """

def render_mlb_info(info: Dict) -> str:
    """Render MLB-specific game info."""
    on_first = bool(info.get("onFirst"))
    on_second = bool(info.get("onSecond"))
    on_third = bool(info.get("onThird"))

    first_class = "mlb-occupied" if on_first else "mlb-empty"
    second_class = "mlb-occupied" if on_second else "mlb-empty"
    third_class = "mlb-occupied" if on_third else "mlb-empty"

    first_symbol = "●" if on_first else "○"
    second_symbol = "●" if on_second else "○"
    third_symbol = "●" if on_third else "○"

    occupied_color = "#00C853"
    empty_color = "#F5F5F5"
    first_inline = occupied_color if on_first else empty_color
    second_inline = occupied_color if on_second else empty_color
    third_inline = occupied_color if on_third else empty_color
    
    return f"""
    <div class='info-panel'>
        <div class='info-title'>MLB Live Situation</div>
        ⚾ Inning: {escape(str(info.get('inning', '')))}<br>
        🧢 At Bat: {escape(str(info.get('at_bat', 'N/A')))}<br>
        🥎 Pitcher: {escape(str(info.get('pitcher', 'N/A')))}<br>
        🎯 Count: {escape(str(info.get('balls', 0)))} Balls, {escape(str(info.get('strikes', 0)))} Strikes<br><br>
        <div class='mlb-diamond-wrap' style='display:inline-block; padding:12px 16px; border-radius:10px; background:linear-gradient(135deg, #1b5e20, #2e7d32);'>
            <table class='mlb-diamond-table' style='margin:0 auto; border-collapse:collapse;'>
                <tr>
                    <td style='width:40px; text-align:center;'></td>
                    <td class='mlb-base {second_class}' style='width:40px; text-align:center; font-size:24px; line-height:1; color:{second_inline};'>{second_symbol}</td>
                    <td style='width:40px; text-align:center;'></td>
                </tr>
                <tr>
                    <td class='mlb-base {third_class}' style='width:40px; text-align:center; font-size:24px; line-height:1; color:{third_inline};'>{third_symbol}</td>
                    <td class='mlb-home' style='width:40px; text-align:center; color:white; font-weight:bold;'>◆</td>
                    <td class='mlb-base {first_class}' style='width:40px; text-align:center; font-size:24px; line-height:1; color:{first_inline};'>{first_symbol}</td>
                </tr>
                <tr>
                    <td style='width:40px; text-align:center;'></td>
                    <td class='mlb-home' style='width:40px; text-align:center; color:white; font-weight:bold;'>H</td>
                    <td style='width:40px; text-align:center;'></td>
                </tr>
            </table>
        </div>
    </div>
    """

def render_field_position(yard_line: str) -> str:
    """Render a visual field position indicator."""
    if not yard_line:
        return "<div style='text-align: center; color: #6b7280;'>No field position data</div>"
    
    # Parse yard line (e.g., "50", "20" means 20 yards from endzone)
    try:
        match = re.search(r"\d+", str(yard_line))
        if not match:
            return "<div style='text-align: center; color: #6b7280;'>No field position data</div>"
        yards = int(match.group())
        # Convert 0-50 yard-line values into 0-100 display space and clamp
        position_percent = max(0, min(100, yards * 2))
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
    
    truncated_text = last_play_text[:150] + "..." if len(last_play_text) > 150 else last_play_text
    display_text = escape(truncated_text)
    
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


def render_betiq_odds(odds: Optional[Dict[str, Any]]) -> str:
    """Render BetIQ odds when available."""
    if not odds:
        return ""

    spread = escape(str(odds.get("spread", "N/A")))
    total = escape(str(odds.get("total", "N/A")))

    return f"""
    <div class='info-panel odds-panel'>
        <div class='info-title'>BetIQ Market</div>
        <div class='odds-grid'>
            <div class='odds-chip'>
                <div class='odds-chip-label'>Spread</div>
                <div class='odds-chip-value'>{spread}</div>
            </div>
            <div class='odds-chip'>
                <div class='odds-chip-label'>Total</div>
                <div class='odds-chip-value'>{total}</div>
            </div>
        </div>
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

def render_game_card(game: GameInfo, odds_refresh_key: int = 0):
    """Render a single game card."""
    col1, col2, col3 = st.columns([3, 2, 3])
    game_odds = find_game_odds(
        game.league,
        game.away_team.name,
        game.home_team.name,
        refresh_key=odds_refresh_key,
    )
    away_moneyline = game_odds.get("ml_away") if game_odds else None
    home_moneyline = game_odds.get("ml_home") if game_odds else None
    
    with col1:
        st.markdown(
            render_team_card(game.away_team, align="right", moneyline=away_moneyline),
            unsafe_allow_html=True,
        )
    
    with col2:
        st.markdown(
            f"<div style='text-align:center; margin-bottom:8px;'><span class='league-badge'>{escape(str(game.league))}</span></div>",
            unsafe_allow_html=True,
        )
        renderer = get_info_renderer(game.league)
        st.markdown(renderer(game.info) + render_betiq_odds(game_odds), unsafe_allow_html=True)
    
    with col3:
        st.markdown(
            render_team_card(game.home_team, align="left", moneyline=home_moneyline),
            unsafe_allow_html=True,
        )
    
    display_game_details(
        {
            "sport": game.league,
            "away_team": {"name": game.away_team.name, "score": game.away_team.score},
            "home_team": {"name": game.home_team.name, "score": game.home_team.score},
            "info": game.info,
            "odds": game_odds or {},
        }
    )

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
                render_betting_table(
                    league,
                    empty_message=f"No betting data for {league.upper()} yet.",
                )
            except Exception as e:
                st.warning(f"Could not load {league.upper()} data: {str(e)[:100]}")


def render_nfl_section(games: List[GameInfo]):
    """Render a dedicated NFL section with live games and betting predictions."""
    st.markdown(
        "<div class='section-header'><h3>🏈 NFL Live Games & Betting</h3></div>",
        unsafe_allow_html=True,
    )

    _, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔁 Refresh NFL", key="refresh_nfl"):
            st.session_state.nfl_refresh_key = st.session_state.get("nfl_refresh_key", 0) + 1
            st.rerun()

    nfl_refresh_key = st.session_state.get("nfl_refresh_key", 0)
    nfl_games = (
        fetch_espn_league_scores("football/nfl", refresh_key=nfl_refresh_key)
        if nfl_refresh_key
        else [game for game in games if game.league == "nfl"]
    )

    st.markdown(
        "<div class='section-header'><h3>🏈 NFL Live Games</h3></div>",
        unsafe_allow_html=True,
    )
    if nfl_games:
        for game in nfl_games:
            render_game_card(game, odds_refresh_key=nfl_refresh_key)
            st.divider()
    else:
        st.info("No live NFL games currently.")

    st.markdown(
        "<div class='section-header'><h3>📊 NFL Betting Predictions</h3></div>",
        unsafe_allow_html=True,
    )
    try:
        render_betting_table(
            "nfl",
            empty_message="No NFL betting data available yet.",
            recommendation_col="Recommended Bet",
            refresh_key=nfl_refresh_key,
        )
    except Exception as e:
        st.warning(f"Could not load NFL data: {str(e)[:100]}")

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
                    f"<span style='display:flex; align-items:center; margin-right:6px;'>"
                    f"<img src='{escape(config['icon'])}' width='30' style='vertical-align:middle;' alt='{escape(sport)} icon'>"
                    f"</span>"
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
st.markdown("---")
render_nfl_section(games)
