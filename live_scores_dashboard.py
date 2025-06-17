import streamlit as st
import requests
import time
from datetime import datetime, date


TEAM_COLORS = {
    # MLB
    "New York Yankees": ["#132448", "#C4CED4"],
    "Boston Red Sox": ["#BD3039", "#0C2340"],
    "Los Angeles Dodgers": ["#005A9C", "#EF3E42"],

    # NFL
    "Dallas Cowboys": ["#041E42", "#869397"],
    "Kansas City Chiefs": ["#E31837", "#FFB81C"],
    "Green Bay Packers": ["#203731", "#FFB612"],

    # NBA
    "Los Angeles Lakers": ["#552583", "#FDB927"],
    "Boston Celtics": ["#007A33", "#BA9653"],
    "Golden State Warriors": ["#1D428A", "#FFC72C"],

    # WNBA
    "Las Vegas Aces": ["#000000", "#C8102E"],
    "New York Liberty": ["#17B3A6", "#000000"],
    "Seattle Storm": ["#2E8B57", "#FFC72C"],

    # NHL
    "Toronto Maple Leafs": ["#00205B", "#FFFFFF"],
    "Chicago Blackhawks": ["#CF0A2C", "#000000"],
    "Boston Bruins": ["#FFB81C", "#000000"],
}

def get_team_colors(team_name):
    return TEAM_COLORS.get(team_name, ["#333", "#555"])

@st.cache_data(ttl=60)
def fetch_espn_scores(selected_date):
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
            event_date = datetime.fromisoformat(event["date"].replace("Z", "+00:00")).date()
            if event_date != selected_date:
                continue
            competition = event.get("competitions", [{}])[0]
            competitors = competition.get("competitors", [])
            if len(competitors) < 2:
                continue

            away = next((team for team in competitors if team["homeAway"] == "away"), None)
            home = next((team for team in competitors if team["homeAway"] == "home"), None)

            away_name = away["team"]["displayName"]
            home_name = home["team"]["displayName"]

            info = {}
            status = competition.get("status", {})
            situation = competition.get("situation", {})
            if league_slug == "mlb":
                info = {
                    "inning": status.get("type", {}).get("shortDetail", ""),
                    "at_bat": situation.get("lastPlay", {}).get("athlete", {}).get("displayName", "N/A"),
                    "pitcher": situation.get("pitcher", {}).get("athlete", {}).get("displayName", "N/A")
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
                "away_team": {
                    "name": away_name,
                    "score": away.get("score", "0"),
                    "colors": get_team_colors(away_name)
                },
                "home_team": {
                    "name": home_name,
                    "score": home.get("score", "0"),
                    "colors": get_team_colors(home_name)
                },
                "info": info
            })
    return games

st.set_page_config(layout="wide")
st.title("\U0001F3DF\ufe0f Live American Sports Scoreboard")

selected_day = st.date_input("Select Date", value=date.today())

st.markdown("""
    <style>
        @media only screen and (max-width: 768px) {
            .element-container:nth-child(2n+1) .block-container { flex-direction: column !important; }
            .scoreboard-column, .info-box { font-size: 18px !important; padding: 10px !important; }
            h3 { font-size: 20px !important; }
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
        hr {
            border: none;
            height: 2px;
            background-color: #888;
            margin: 30px 0;
        }
    </style>
""", unsafe_allow_html=True)


games = fetch_espn_scores(selected_day)
for game in games:
    col1, col2, col3 = st.columns([3, 2, 3])

    away_team = game["away_team"]
    home_team = game["home_team"]
    info = game["info"]

    with col1:
        st.markdown(f"""
            <div class='scoreboard-column' style='background: linear-gradient(135deg, {away_team['colors'][0]}, {away_team['colors'][1]});'>
                <h3>{away_team['name']}</h3>
                <p style='font-size: 36px; margin: 10px 0;'>{away_team['score']}</p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        if game['sport'] == 'mlb':
            st.markdown(f"""
                <div class='info-box'>
                    ⚾ <strong>Inning:</strong> {info.get('inning', '')}<br/>
                    🧢 <strong>At Bat:</strong> {info.get('at_bat', '')}<br/>
                    🥎 <strong>Pitcher:</strong> {info.get('pitcher', '')}
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
                <p style='font-size: 36px; margin: 10px 0;'>{home_team['score']}</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr/>", unsafe_allow_html=True)
