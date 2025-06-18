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
    </style>
""", unsafe_allow_html=True)





games = fetch_espn_scores()

# Determine available sports in today's games
available_sports = sorted(set(game.get("sport", "").upper() for game in games))

# Mapping sport names to logos
sport_icons = {
    "NBA": "https://a.espncdn.com/i/teamlogos/leagues/500/nba.png",
    "WNBA": "https://a.espncdn.com/i/teamlogos/leagues/500/wnba.png",
    "NFL": "https://a.espncdn.com/i/teamlogos/leagues/500/nfl.png",
    "NHL": "https://a.espncdn.com/i/teamlogos/leagues/500/nhl.png",
    "MLB": "https://a.espncdn.com/i/teamlogos/leagues/500/mlb.png"
}

if "selected_sport" not in st.session_state:
    st.session_state.selected_sport = available_sports[0] if available_sports else None

# Create tab labels with icons using markdown and HTML
tab_labels = []
for sport in available_sports:
    icon_url = sport_icons.get(sport, "")
    # Label with inline image + text
    label = f"<img src='{icon_url}' height='20' style='vertical-align:middle;margin-right:8px;'/> {sport}"
    tab_labels.append(label)

# Use st.tabs with sanitized plain labels, but show icons in headers manually after
tabs = st.tabs(available_sports)

for i, sport in enumerate(available_sports):
    with tabs[i]:
        st.markdown(f"<h2 style='display:flex; align-items:center; gap:8px;'>"
                    f"<img src='{sport_icons.get(sport)}' height='32'/> {sport} Games</h2>", unsafe_allow_html=True)

        filtered_games = [game for game in games if game.get("sport", "").upper() == sport]

        if "expanded_game" not in st.session_state:
            st.session_state.expanded_game = None

        for idx, game in enumerate(filtered_games):
            away_team = game.get("away_team", {})
            home_team = game.get("home_team", {})
            info = game.get("info", {})

            game_id = f"{game.get('start_time', '')}_{away_team.get('abbreviation', '')}_{home_team.get('abbreviation', '')}".replace(" ", "_")

            col1, col2, col3 = st.columns([3, 2, 3])

            with col1:
                st.markdown(f"""
                    <div class='scoreboard-column' style='background: linear-gradient(135deg, {away_team.get('colors', ['#000000', '#111111'])[0]}, {away_team.get('colors', ['#000000', '#111111'])[1]});'>
                        <h3>{away_team.get('name', 'Away')}</h3>
                        <img src="{away_team.get('logo', '')}" class="team-logo"/>
                        <p style='font-size: 36px; margin: 10px 0;'>{away_team.get('score', '')}</p>
                    </div>
                """, unsafe_allow_html=True)

            with col2:
                container = st.container()
                if container.button(" ", key=f"expand_button_{sport}_{idx}"):
                    if st.session_state.expanded_game == game_id:
                        st.session_state.expanded_game = None
                    else:
                        st.session_state.expanded_game = game_id
                    st.experimental_rerun()

                with container:
                    if st.session_state.expanded_game == game_id:
                        display_game_details(game)
                    else:
                        sport_lower = sport.lower()
                        if sport_lower == 'mlb':
                            first = 'active' if info.get('onFirst') else ''
                            second = 'active' if info.get('onSecond') else ''
                            third = 'active' if info.get('onThird') else ''
                            st.markdown(f"""
                                <div class='info-box'>
                                    ⚾ <strong>Inning:</strong> {info.get('inning', '')}<br/>
                                    🧢 <strong>At Bat:</strong> {info.get('at_bat', '')}<br/>
                                    🥎 <strong>Pitcher:</strong> {info.get('pitcher', '')}
                                    <div class='diamond'>
                                        <div class='base second {second}'></div>
                                        <div class='base third {third}'></div>
                                        <div class='base first {first}'></div>
                                        <div class='base mound'></div>
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)
                        elif sport_lower == 'nfl':
                            st.markdown(f"""
                                <div class='info-box'>
                                    🏈 <strong>Quarter:</strong> {info.get('quarter', '')}<br/>
                                    🟢 <strong>Possession:</strong> {info.get('possession', '')}
                                </div>
                            """, unsafe_allow_html=True)
                        elif sport_lower in ['nba', 'wnba']:
                            st.markdown(f"""
                                <div class='info-box'>
                                    🏀 <strong>Quarter:</strong> {info.get('quarter', '')}<br/>
                                    ⏱️ <strong>Clock:</strong> {info.get('clock', '')}
                                </div>
                            """, unsafe_allow_html=True)
                        elif sport_lower == 'nhl':
                            st.markdown(f"""
                                <div class='info-box'>
                                    🏒 <strong>{info.get('period', '')}</strong><br/>
                                    ⏱️ <strong>Clock:</strong> {info.get('clock', '')}
                                </div>
                            """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                    <div class='scoreboard-column' style='background: linear-gradient(135deg, {home_team.get('colors', ['#000000', '#111111'])[0]}, {home_team.get('colors', ['#000000', '#111111'])[1]});'>
                        <h3>{home_team.get('name', 'Home')}</h3>
                        <img src="{home_team.get('logo', '')}" class="team-logo"/>
                        <p style='font-size: 36px; margin: 10px 0;'>{home_team.get('score', '')}</p>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("<hr/>", unsafe_allow_html=True)
