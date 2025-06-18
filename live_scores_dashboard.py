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

for game in filtered_games:
    away_team = game["away_team"]
    home_team = game["home_team"]
    info = game.get("info", {})
    sport_lower = game.get("sport", "").lower()

    with st.container():
        st.markdown(
            f"""
            <style>
                .score-box {{
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                    border: 1px solid #ccc;
                    border-radius: 12px;
                    padding: 12px;
                    background: #f9f9f9;
                    margin-bottom: 16px;
                }}
                .team-box {{
                    display: flex;
                    justify-content: space-between;
                    flex-wrap: wrap;
                    gap: 16px;
                }}
                .team {{
                    flex: 1;
                    min-width: 140px;
                    border-radius: 10px;
                    padding: 10px;
                    text-align: center;
                    color: #fff;
                }}
                .info-panel {{
                    font-size: 14px;
                    margin-top: 6px;
                }}
                .diamond {{
                    position: relative;
                    width: 100px;
                    height: 100px;
                    margin: 10px auto;
                    transform: rotate(45deg);
                }}
                .base {{
                    width: 20px;
                    height: 20px;
                    background-color: #ccc;
                    position: absolute;
                    border-radius: 3px;
                }}
                .base.active {{
                    background-color: #27ae60;
                }}
                .first {{
                    top: 70px;
                    left: 70px;
                }}
                .second {{
                    top: 0;
                    left: 70px;
                }}
                .third {{
                    top: 0;
                    left: 0;
                }}
                .mound {{
                    top: 35px;
                    left: 35px;
                    width: 30px;
                    height: 30px;
                    background-color: #34495e;
                    border-radius: 50%;
                }}
                @media (max-width: 480px) {{
                    .team {{
                        min-width: 100%;
                    }}
                    .diamond {{
                        transform: scale(0.8) rotate(45deg);
                    }}
                }}
            </style>

            <div class="score-box">
                <div class="team-box">
                    <div class="team" style="background: linear-gradient(135deg, {away_team['colors'][0]}, {away_team['colors'][1]});">
                        <h4>{away_team['name']}</h4>
                        <img src="{away_team['logo']}" style="width: 60px; max-width: 100%;" />
                        <p style="font-size: 28px; margin: 8px 0;">{away_team['score']}</p>
                    </div>

                    <div class="team" style="background: linear-gradient(135deg, {home_team['colors'][0]}, {home_team['colors'][1]});">
                        <h4>{home_team['name']}</h4>
                        <img src="{home_team['logo']}" style="width: 60px; max-width: 100%;" />
                        <p style="font-size: 28px; margin: 8px 0;">{home_team['score']}</p>
                    </div>
                </div>
        """,
            unsafe_allow_html=True,
        )

        # MLB Info with diamond
        if sport_lower == "mlb":
            first = 'active' if info.get('onFirst') else ''
            second = 'active' if info.get('onSecond') else ''
            third = 'active' if info.get('onThird') else ''
            at_bat = info.get('at_bat', 'N/A')
            pitcher = info.get('pitcher', 'N/A')

            st.markdown(f"""
                <div class="info-panel">
                    ⚾ <strong>Inning:</strong> {info.get('inning', '')}<br/>
                    🧢 <strong>At Bat:</strong> {at_bat}<br/>
                    🥎 <strong>Pitcher:</strong> {pitcher}
                    <div class="diamond">
                        <div class="base first {first}"></div>
                        <div class="base second {second}"></div>
                        <div class="base third {third}"></div>
                        <div class="base mound"></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # NBA / WNBA
        elif sport_lower in ["nba", "wnba"]:
            st.markdown(f"""
                <div class="info-panel">
                    ⛹️‍♂️ <strong>Quarter:</strong> {info.get('quarter', 'N/A')}<br/>
                    ⏱️ <strong>Clock:</strong> {info.get('clock', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # NFL
        elif sport_lower == "nfl":
            st.markdown(f"""
                <div class="info-panel">
                    🏈 <strong>Quarter:</strong> {info.get('quarter', 'N/A')}<br/>
                    🟢 <strong>Possession:</strong> {info.get('possession', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

        # NHL
        elif sport_lower == "nhl":
            st.markdown(f"""
                <div class="info-panel">
                    🏒 <strong>Period:</strong> {info.get('period', 'N/A')}<br/>
                    ⏱️ <strong>Clock:</strong> {info.get('clock', '')}
                </div>
            </div>
            """, unsafe_allow_html=True)

        else:
            st.markdown("</div>")
