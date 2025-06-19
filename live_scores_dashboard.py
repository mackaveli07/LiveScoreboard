import streamlit as st
import requests
import time
from datetime import datetime, date
from team_colors_all_leagues import team_colors as TEAM_COLORS
from all_team_logos import team_logos as TEAM_LOGOS
from pathlib import Path
from expandable_game_view import display_game_details

sports = ['mlb', 'nfl', 'nba', 'wnba', 'nhl']


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
            background: #3F9B0B;
            transform: rotate(45deg);
            transform-origin: center;
            z-index: 0;
        }
        .base {
            position: absolute;
            width: 20px;
            height: 20px;
            background-color: #FFFFFF;
            border-radius: 50%;
            z-index: 1;
        }
        .base.active {
            background-color: limegreen;
        }
        .second { top: -10px; left: 40px; }
        .third { top: 40px; left: -10px; }
        .first { top: 40px; left: 90px; }
        .mound { top: 40px; left: 40px; background-color: #964B00; }
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
            opacity: 0.50;
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



sport_icons = {
    "NBA": "https://a.espncdn.com/i/teamlogos/leagues/500/nba.png",
    "WNBA": "https://a.espncdn.com/i/teamlogos/leagues/500/wnba.png",
    "NFL": "https://a.espncdn.com/i/teamlogos/leagues/500/nfl.png",
    "NHL": "https://a.espncdn.com/i/teamlogos/leagues/500/nhl.png",
    "MLB": "https://a.espncdn.com/i/teamlogos/leagues/500/mlb.png",
}

selected_date = st.date_input("Select date to view games", datetime.now().date(), key="game_date_filter")

# Dummy fallback if fetch_espn_scores() is undefined
try:
    games = fetch_espn_scores()
except NameError:
    games = []

# Ensure session state
if "expanded_game" not in st.session_state:
    st.session_state.expanded_game = None

def filter_games_by_date(games, sport, date):
    filtered = []
    for g in games:
        if g.get('sport', '').lower() != sport:
            continue
        start_time = g.get('start_time')
        if not start_time:
            continue
        try:
            game_date = datetime.fromisoformat(start_time).date()
            if game_date == date:
                filtered.append(g)
        except Exception:
            continue
    return filtered

def get_next_games(games, sport):
    now = datetime.now()
    upcoming = []
    for g in games:
        if g.get('sport', '').lower() != sport:
            continue
        start_time = g.get('start_time')
        if not start_time:
            continue
        try:
            dt = datetime.fromisoformat(start_time)
            if dt > now:
                upcoming.append(g)
        except Exception:
            continue
    upcoming.sort(key=lambda g: g.get('start_time', ''))
    return upcoming[:3]

def display_game_details(game):
    st.write("Expanded game details for:", game.get('away_team', {}).get('name'), "vs", game.get('home_team', {}).get('name'))

def display_games(games):
    for idx, game in enumerate(games):
        away_team = game.get("away_team", {})
        home_team = game.get("home_team", {})
        info = game.get("info", {})

        game_id = f"{game.get('start_time', '')}_{away_team.get('abbreviation', '')}_{home_team.get('abbreviation', '')}_{idx}".replace(" ", "_")

        col1, col2, col3 = st.columns([3, 2, 3])

        with col1:
            st.markdown(f"""
                <div class='scoreboard-column' style='background: linear-gradient(135deg, {away_team.get('colors', ['#ccc', '#999'])[0]}, {away_team.get('colors', ['#ccc', '#999'])[1]});'>
                    <h3>{away_team.get('name', 'Away')}</h3>
                    <img src="{away_team.get('logo', '')}" class="team-logo"/>
                    <p style='font-size: 36px; margin: 10px 0;'>{away_team.get('score', 0)}</p>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            if st.session_state.expanded_game == game_id:
                display_game_details(game)
                if st.button("Collapse View", key=f"collapse_{game_id}"):
                    st.session_state.expanded_game = None
                    st.experimental_rerun()
            else:
                if st.button("Show More", key=f"expand_{game_id}"):
                    st.session_state.expanded_game = game_id
                    st.experimental_rerun()
                else:
                    sport = game.get("sport", "").lower()
                    if sport == 'mlb':
                        first = 'active' if info.get('onFirst') else ''
                        second = 'active' if info.get('onSecond') else ''
                        third = 'active' if info.get('onThird') else ''
                        at_bat = info.get('at_bat', 'N/A')
                        pitcher = info.get('pitcher', 'N/A')

                        st.markdown(f"""
                            <div class='info-box'>
                                ⚾ <strong>Inning:</strong> {info.get('inning', '')}<br/>
                                🧢 <strong>At Bat:</strong> {at_bat}<br/>
                                🥎 <strong>Pitcher:</strong> {pitcher}
                                <div class='diamond'>
                                    <div class='base second {second}'></div>
                                    <div class='base third {third}'></div>
                                    <div class='base first {first}'></div>
                                    <div class='base mound'></div>
                                </div>
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

        with col3:
            st.markdown(f"""
                <div class='scoreboard-column' style='background: linear-gradient(135deg, {home_team.get('colors', ['#ccc', '#999'])[0]}, {home_team.get('colors', ['#ccc', '#999'])[1]}); border-radius: 10px; padding: 10px;'>
                    <h3>{home_team.get('name', 'Home')}</h3>
                    <img src="{home_team.get('logo', '')}" width="100" />
                    <p style='font-size: 36px; margin: 10px 0;'>{home_team.get('score', 0)}</p>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<hr/>", unsafe_allow_html=True)

tabs = st.tabs([sport.upper() for sport in sports])

for tab, sport in zip(tabs, sports):
    with tab:
        filtered_games = filter_games_by_date(games, sport, selected_date)
        if filtered_games:
            st.write(f"Games on {selected_date.strftime('%Y-%m-%d')} for {sport.upper()}")
            display_games(filtered_games)
        else:
            if selected_date <= datetime.now().date():
                next_games = get_next_games(games, sport)
                if next_games:
                    st.write(f"No games on {selected_date.strftime('%Y-%m-%d')}. Showing next upcoming {sport.upper()} games instead.")
                    display_games(next_games)
                else:
                    st.write(f"No {sport.upper()} games on {selected_date.strftime('%Y-%m-%d')} or upcoming soon.")
            else:
                st.write(f"No {sport.upper()} games on {selected_date.strftime('%Y-%m-%d')}.")
