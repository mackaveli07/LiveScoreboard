import streamlit as st
import requests
import time
from datetime import datetime, date
from team_colors_all_leagues import team_colors as TEAM_COLORS
from all_team_logos import team_logos as TEAM_LOGOS


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
    for sport_path in sports:
        response = requests.get(f"{base_url}/{sport_path}/scoreboard")
        if response.status_code != 200:
            continue
        data = response.json()
        league_slug = sport_path.split("/")[1]
        for event in data.get("events", []):
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

st.set_page_config(layout="wide")
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
for game in games:
    col1, col2, col3 = st.columns([3, 2, 3])

    away_team = game["away_team"]
    home_team = game["home_team"]
    info = game["info"]

    with col1:
        st.markdown(f"""
            <div class='scoreboard-column' style='background: linear-gradient(135deg, {away_team['colors'][0]}, {away_team['colors'][1]});'>
                <h3>{away_team['name']}</h3>
                <img src="{away_team['logo']}" class="team-logo"/>
                <p style='font-size: 36px; margin: 10px 0;'>{away_team['score']}</p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        if game['sport'] == 'mlb':
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
        elif game['sport'] == 'nfl':
            st.markdown(f"""
                <div class='info-box'>
                    🏈 <strong>Quarter:</strong> {info.get('quarter', '')}<br/>
                    🟢 <strong>Possession:</strong> {info.get('possession', '')}
                </div>
            """, unsafe_allow_html=True)
        elif game['sport'] in ['nba', 'wnba']:
            st.markdown(f"""
                <div class='info-box'>
                    🏀 <strong>Quarter:</strong> {info.get('quarter', '')}<br/>
                    ⏱️ <strong>Clock:</strong> {info.get('clock', '')}
                </div>
            """, unsafe_allow_html=True)
        elif game['sport'] == 'nhl':
            st.markdown(f"""
                <div class='info-box'>
                    🏒 <strong>{info.get('period', '')}</strong><br/>
                    ⏱️ <strong>Clock:</strong> {info.get('clock', '')}
                </div>
            """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class='scoreboard-column' style='background: linear-gradient(135deg, {home_team['colors'][0]}, {home_team['colors'][1]});'>
                <h3>{home_team['name']}</h3>
                <img src="{home_team['logo']}" class="team-logo"/>
                <p style='font-size: 36px; margin: 10px 0;'>{home_team['score']}</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
