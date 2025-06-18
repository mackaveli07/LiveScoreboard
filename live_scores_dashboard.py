import streamlit as st
import requests
import time
from datetime import datetime, date
from team_colors_all_leagues import team_colors as TEAM_COLORS
from all_team_logos import team_logos as TEAM_LOGOS
from pathlib import Path
from expandable_game_view import display_game_details


st.set_page_config(page_title="Live Sports Scoreboard", layout="wide")
st.markdown(Path("styles.html").read_text(), unsafe_allow_html=True)

# Basic auto-refresh logic without external packages
if "expanded_game" not in st.session_state:
    st.session_state.expanded_game = None

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()

if st.session_state.expanded_game is None:
    st.session_state.last_refresh = datetime.now()

    if "just_reran" not in st.session_state or not st.session_state.just_reran:
        st.session_state.just_reran = True
        st.rerun()  # 👈 use this instead of st.experimental_rerun()
    else:
        st.session_state.just_reran = False
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

@st.cache_data(ttl=60)
def fetch_espn_scores():
    base_url = "https://site.api.espn.com/apis/site/v2/sports"
    sports = [
        "baseball/mlb", "football/nfl", "basketball/nba",
        "basketball/wnba", "hockey/nhl"
    ]
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

st.title("\U0001F3DF️ Live American Sports Scoreboard")

st.markdown("""
    <style>
        @media only screen and (max-width: 768px) {
            .block-container {
                padding: 1rem !important;
            }
            .scoreboard-column, .info-box {
                font-size: 16px !important;
                padding: 8px !important;
            }
            h3 {
                font-size: 18px !important;
            }
            .diamond {
                transform: scale(0.8);
            }
        }
        .scoreboard-column {
            border-radius: 16px;
            padding: 20px;
            color: white;
            text-align: center;
            font-size: 24px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.3);
        }
        .info-box {
            background-color: #222;
            border: 2px solid #888;
            border-radius: 12px;
            padding: 15px;
            color: #eee;
            font-size: 18px;
        }
        .diamond {
            position: relative;
            width: 100px;
            height: 100px;
            margin: 10px auto;
        }
        .diamond:before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: #444;
            transform: rotate(45deg);
            transform-origin: center;
            z-index: 0;
        }
        .base {
            position: absolute;
            width: 20px;
            height: 20px;
            background-color: #ccc;
            border-radius: 50%;
            z-index: 1;
        }
        .base.active {
            background-color: limegreen;
        }
        .second { top: -10px; left: 40px; }
        .third { top: 40px; left: -10px; }
        .first { top: 40px; left: 90px; }
        .mound { top: 40px; left: 40px; background-color: #888; }
        hr {
            border: none;
            height: 2px;
            background-color: #888;
            margin: 30px 0;
        }
        .team-logo {
            width: 60px;
            height: 60px;
            object-fit: contain;
            opacity: 0.85;
            margin-top: 10px;
        }

        <style>
    /* Tab container */
    [role="tablist"] {
        display: flex;
        gap: 1rem;
        justify-content: center;
        margin-bottom: 1.5rem;
    }
    /* Tab buttons */
    [role="tablist"] > button {
        background-color: #222222;
        color: #eee;
        border-radius: 12px;
        padding: 8px 18px;
        font-size: 1.1rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
        transition: background-color 0.25s ease, color 0.25s ease;
        border: none;
        outline: none;
        cursor: pointer;
        box-shadow: 0 0 8px rgba(255,255,255,0.1);
    }
    /* Active tab */
    [role="tablist"] > button[aria-selected="true"] {
        background-color: #0a84ff;
        color: white;
        box-shadow: 0 0 15px #0a84ff;
    }
    /* Hover on inactive tabs */
    [role="tablist"] > button:hover:not([aria-selected="true"]) {
        background-color: #444444;
        color: #ddd;
    }
    /* Icon inside tab */
    [role="tablist"] > button img {
        height: 28px;
        width: 28px;
        border-radius: 4px;
        object-fit: contain;
    }
    </style>
""", unsafe_allow_html=True)





games = fetch_espn_scores()

available_sports = sorted(set(game.get("sport", "").upper() for game in games))

sport_icons = {
    "NBA": "https://a.espncdn.com/i/teamlogos/leagues/500/nba.png",
    "WNBA": "https://a.espncdn.com/i/teamlogos/leagues/500/wnba.png",
    "NFL": "https://a.espncdn.com/i/teamlogos/leagues/500/nfl.png",
    "NHL": "https://a.espncdn.com/i/teamlogos/leagues/500/nhl.png",
    "MLB": "https://a.espncdn.com/i/teamlogos/leagues/500/mlb.png"
}

# Add the betting tab as a special tab key "BET"
tabs_keys = available_sports + ["Betting Odds"]

tabs = st.tabs(tabs_keys)

for i, tab_key in enumerate(tabs_keys):
    with tabs[i]:
        if tab_key == "BET":
            st.markdown("<h2>💰 Betting Info</h2>", unsafe_allow_html=True)
            # Put your betting info display code here
            st.write("Display your betting odds, lines, or other info here.")
        else:
            sport = tab_key
            icon_url = sport_icons.get(sport, "")
            st.markdown(f"<h2 style='display:flex; align-items:center; gap:8px;'>"
                        f"<img src='{icon_url}' height='32'/> {sport} Games</h2>", unsafe_allow_html=True)

            filtered_games = [game for game in games if game.get("sport", "").upper() == sport]

            if "expanded_game" not in st.session_state:
                st.session_state.expanded_game = None

            for idx, game in enumerate(filtered_games):
                away_team = game.get("away_team", {})
                home_team = game.get("home_team", {})
                info = game.get("info", {})
            
                sport = game.get("sport", "").lower()
            
                col1, col2, col3 = st.columns([3, 2, 3])
            
                # Away team column with basic stats below score
                with col1:
                   st.markdown(f"""
                        <div class='scoreboard-column' style='background: linear-gradient(135deg, {away_team.get('colors', ['#000000', '#111111'])[0]}, {away_team.get('colors', ['#000000', '#111111'])[1]}); padding: 10px; border-radius: 10px;'>
                            <h3>{away_team.get('name', 'Away')}</h3>
                            <img src="{away_team.get('logo', '')}" class="team-logo"/>
                            <p style='font-size: 36px; margin: 10px 0;'>{away_team.get('score', '')}</p>
                            <div style="display: flex; gap: 15px; font-size: 16px; margin-top: 8px;">
                                {"".join([
                                    f"<div>🧢 <strong>At Bat:</strong> {info.get('at_bat', '')}</div>" if sport == 'mlb' else '',
                                    f"<div>🥎 <strong>Pitcher:</strong> {info.get('pitcher', '')}</div>" if sport == 'mlb' else '',
                                    f"<div>🏈 <strong>Quarter:</strong> {info.get('quarter', '')}</div>" if sport == 'nfl' else '',
                                    f"<div>🟢 <strong>Possession:</strong> {info.get('possession', '')}</div>" if sport == 'nfl' else '',
                                    f"<div>🏀 <strong>Quarter:</strong> {info.get('quarter', '')}</div>" if sport in ['nba', 'wnba'] else '',
                                    f"<div>⏱️ <strong>Clock:</strong> {info.get('clock', '')}</div>" if sport in ['nba', 'wnba'] else '',
                                    f"<div>🏒 <strong>{info.get('period', '')}</strong></div>" if sport == 'nhl' else '',
                                    f"<div>⏱️ <strong>Clock:</strong> {info.get('clock', '')}</div>" if sport == 'nhl' else '',
                                ])}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
            
                    # Show basic away team stats (customize per sport)
                        if sport == 'mlb':
                            st.markdown(f"""
                                <div class='info-box'>
                                    🧢 <strong>At Bat:</strong> {info.get('at_bat', '')}<br/>
                                    🥎 <strong>Pitcher:</strong> {info.get('pitcher', '')}
                                </div>
                            """, unsafe_allow_html=True)
                        elif sport == 'nfl':
                            st.markdown(f"""
                                <div class='info-box'>
                                    🏈 <strong>Quarter:</strong> {info.get('quarter', '')}<br/>
                                    🟢 <strong>Possession:</strong> {info.get('possession', '')}
                                </div>
                            """, unsafe_allow_html=True)
                        elif sport in ['nba', 'wnba']:
                            st.markdown(f"""
                                <div class='info-box'>
                                    🏀 <strong>Quarter:</strong> {info.get('quarter', '')}<br/>
                                    ⏱️ <strong>Clock:</strong> {info.get('clock', '')}
                                </div>
                            """, unsafe_allow_html=True)
                        elif sport == 'nhl':
                            st.markdown(f"""
                                <div class='info-box'>
                                    🏒 <strong>{info.get('period', '')}</strong><br/>
                                    ⏱️ <strong>Clock:</strong> {info.get('clock', '')}
                                </div>
                            """, unsafe_allow_html=True)
                
                    # Empty middle column or you can add something if you want
                    with col2:
                        st.markdown(" ")  # keep layout consistent
                
                    # Home team column with basic stats below score
                    with col3:
                        st.markdown(f"""
                            <div class='scoreboard-column' style='background: linear-gradient(135deg, {home_team.get('colors', ['#000000', '#111111'])[0]}, {home_team.get('colors', ['#000000', '#111111'])[1]});'>
                                <h3>{home_team.get('name', 'Home')}</h3>
                                <img src="{home_team.get('logo', '')}" class="team-logo"/>
                                <p style='font-size: 36px; margin: 10px 0;'>{home_team.get('score', '')}</p>
                            </div>
                        """, unsafe_allow_html=True)
                
                        # Show basic home team stats (customize per sport)
                        if sport == 'mlb':
                            st.markdown(f"""
                                <div class='info-box'>
                                    🧢 <strong>At Bat:</strong> {info.get('at_bat', '')}<br/>
                                    🥎 <strong>Pitcher:</strong> {info.get('pitcher', '')}
                                </div>
                            """, unsafe_allow_html=True)
                        elif sport == 'nfl':
                            st.markdown(f"""
                                <div class='info-box'>
                                    🏈 <strong>Quarter:</strong> {info.get('quarter', '')}<br/>
                                    🟢 <strong>Possession:</strong> {info.get('possession', '')}
                                </div>
                            """, unsafe_allow_html=True)
                        elif sport in ['nba', 'wnba']:
                            st.markdown(f"""
                                <div class='info-box'>
                                    🏀 <strong>Quarter:</strong> {info.get('quarter', '')}<br/>
                                    ⏱️ <strong>Clock:</strong> {info.get('clock', '')}
                                </div>
                            """, unsafe_allow_html=True)
                        elif sport == 'nhl':
                            st.markdown(f"""
                                <div class='info-box'>
                                    🏒 <strong>{info.get('period', '')}</strong><br/>
                                    ⏱️ <strong>Clock:</strong> {info.get('clock', '')}
                                </div>
                            """, unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
