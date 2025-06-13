import streamlit as st
import requests
import time
from datetime import datetime
from datetime import date
import streamlit.components.v1 as components

ODDS_API_KEY = "4c39fd0413dbcc55279d85ab18bcc6f0"
if "last_odds_refresh_date" not in st.session_state:
    st.session_state.last_odds_refresh_date = date.today()
else:
    today = date.today()
    if st.session_state.last_odds_refresh_date != today:
        get_odds_data.clear()
        st.session_state.last_odds_refresh_date = today


st.set_page_config(page_title="Live Sports Scores", layout="wide")

# Animation and Styling CSS
st.markdown("""
    <style>
    .blinking {
        animation: blinker 1s linear infinite;
    }
    @keyframes blinkScore {
        0% { opacity: 1; }
        50% { opacity: 0; }
        100% { opacity: 1; }
    }

    .diamond {
        width: 80px;
        height: 80px;
        position: relative;
        margin: 10px auto;
        background: none;
        border: none;
    }
    .base {
        width: 14px;
        height: 14px;
        background-color: white;
        border: 2px solid #999;
        position: absolute;
        transform: rotate(45deg);
        z-index: 2;
    }
    .base.occupied {
        background-color: #228B22;
        border-color: #145214;
    }
    .second {
        top: 0;
        left: 50%;
        transform: translate(-50%, -50%) rotate(45deg);
    }
    .first {
        bottom: 10%;
        right: 0;
        transform: translate(50%, 50%) rotate(45deg);
    }
    .third {
        bottom: 10%;
        left: 0;
        transform: translate(-50%, 50%) rotate(45deg);
    }
    .home {
        bottom: 0;
        left: 50%;
        transform: translate(-50%, 50%) rotate(45deg);
        border-color: transparent;
        border-top: 2px solid #999;
        border-left: 2px solid #999;
        background: none;
    }

    .team-score-wrapper {
        padding: 0.6em;
        margin-top: 0.5em;
        border-radius: 10px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        border: 2px solid black;
        color: white;
        font-weight: bold;
        min-width: 80px;
    }
    .team-name {
        font-size: 1.1em;
        margin-bottom: 0.3em;
        text-align: center;
    }
    .team-score-box {
        font-size: 1.4em;
        text-align: center;
    }
    .scoring-popup {
        animation: fadeOut 2s ease-out forwards;
        font-size: 1.2em;
        color: yellow;
        font-weight: bold;
        position: relative;
        top: -8px;
    }
    @keyframes fadeOut {
        0% { opacity: 1; top: -8px; }
        50% { opacity: 1; top: -20px; }
        100% { opacity: 0; top: -30px; }
    }
    </style>
""", unsafe_allow_html=True)
# --- Sport Logos and Config ---
SPORTS = {
    "NFL (Football)": {
        "path": "football/nfl",
        "icon": "https://upload.wikimedia.org/wikipedia/en/a/a2/National_Football_League_logo.svg",
        "odds_key": "americanfootball_nfl"
    },
    "NBA (Basketball)": {
        "path": "basketball/nba",
        "icon": "https://upload.wikimedia.org/wikipedia/en/0/03/National_Basketball_Association_logo.svg",
        "odds_key": "basketball_nba"
    },
     "MLB (Baseball)": {
        "path": "baseball/mlb",
        "icon": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/MLB_Logo.svg/320px-MLB_Logo.svg",
        "odds_key": "baseball_mlb"
    },
    "NHL (Hockey)": {
        "path": "hockey/nhl",
        "icon": "https://upload.wikimedia.org/wikipedia/en/3/3a/05_NHL_Shield.svg",
        "odds_key": "icehockey_nhl"
    }
}

# --- Display Scores ---
TEAM_COLORS = {
    # MLB
    "Arizona Diamondbacks": {"primary": "#A71930", "secondary": "#E3D4AD"},
    "Atlanta Braves": {"primary": "#CE1141", "secondary": "#13274F"},
    "Baltimore Orioles": {"primary": "#DF4601", "secondary": "#000000"},
    "Boston Red Sox": {"primary": "#BD3039", "secondary": "#0C2340"},
    "Chicago White Sox": {"primary": "#27251F", "secondary": "#C4CED4"},
    "Chicago Cubs": {"primary": "#0E3386", "secondary": "#CC3433"},
    "Cincinnati Reds": {"primary": "#C6011F", "secondary": "#000000"},
    "Cleveland Guardians": {"primary": "#0C2340", "secondary": "#E31937"},
    "Colorado Rockies": {"primary": "#333366", "secondary": "#C4CED4"},
    "Detroit Tigers": {"primary": "#0C2340", "secondary": "#FA4616"},
    "Houston Astros": {"primary": "#002D62", "secondary": "#EB6E1F"},
    "Kansas City Royals": {"primary": "#004687", "secondary": "#C09A5B"},
    "Los Angeles Angels": {"primary": "#BA0021", "secondary": "#003263"},
    "Los Angeles Dodgers": {"primary": "#005A9C", "secondary": "#EF3E42"},
    "Miami Marlins": {"primary": "#00A3E0", "secondary": "#EF3340"},
    "Milwaukee Brewers": {"primary": "#12284B", "secondary": "#FFC52F"},
    "Minnesota Twins": {"primary": "#002B5C", "secondary": "#D31145"},
    "New York Yankees": {"primary": "#003087", "secondary": "#E4002B"},
    "New York Mets": {"primary": "#002D72", "secondary": "#FF5910"},
    "Oakland Athletics": {"primary": "#003831", "secondary": "#EFB21E"},
    "Philadelphia Phillies": {"primary": "#E81828", "secondary": "#002D72"},
    "Pittsburgh Pirates": {"primary": "#FDB827", "secondary": "#27251F"},
    "San Diego Padres": {"primary": "#2F241D", "secondary": "#FFC425"},
    "San Francisco Giants": {"primary": "#FD5A1E", "secondary": "#27251F"},
    "Seattle Mariners": {"primary": "#005C5C", "secondary": "#C4CED4"},
    "St. Louis Cardinals": {"primary": "#C41E3A", "secondary": "#0C2340"},
    "Tampa Bay Rays": {"primary": "#092C5C", "secondary": "#8FBCE6"},
    "Texas Rangers": {"primary": "#003278", "secondary": "#C0111F"},
    "Toronto Blue Jays": {"primary": "#134A8E", "secondary": "#1D2D5C"},
    "Washington Nationals": {"primary": "#AB0003", "secondary": "#11225B"},

    # NFL
    "Arizona Cardinals": {"primary": "#97233F", "secondary": "#FFB612"},
    "Atlanta Falcons": {"primary": "#A71930", "secondary": "#000000"},
    "Baltimore Ravens": {"primary": "#241773", "secondary": "#9E7C0C"},
    "Buffalo Bills": {"primary": "#00338D", "secondary": "#C60C30"},
    "Carolina Panthers": {"primary": "#0085CA", "secondary": "#101820"},
    "Chicago Bears": {"primary": "#0B162A", "secondary": "#C83803"},
    "Cincinnati Bengals": {"primary": "#FB4F14", "secondary": "#000000"},
    "Cleveland Browns": {"primary": "#311D00", "secondary": "#FF3C00"},
    "Dallas Cowboys": {"primary": "#041E42", "secondary": "#869397"},
    "Denver Broncos": {"primary": "#FB4F14", "secondary": "#002244"},
    "Detroit Lions": {"primary": "#0076B6", "secondary": "#B0B7BC"},
    "Green Bay Packers": {"primary": "#203731", "secondary": "#FFB612"},
    "Houston Texans": {"primary": "#03202F", "secondary": "#A71930"},
    "Indianapolis Colts": {"primary": "#002C5F", "secondary": "#A2AAAD"},
    "Jacksonville Jaguars": {"primary": "#006778", "secondary": "#9F792C"},
    "Kansas City Chiefs": {"primary": "#E31837", "secondary": "#FFB81C"},
    "Las Vegas Raiders": {"primary": "#000000", "secondary": "#A5ACAF"},
    "Los Angeles Chargers": {"primary": "#002A5E", "secondary": "#FFC20E"},
    "Los Angeles Rams": {"primary": "#003594", "secondary": "#FFA300"},
    "Miami Dolphins": {"primary": "#008E97", "secondary": "#FC4C02"},
    "Minnesota Vikings": {"primary": "#4F2683", "secondary": "#FFC62F"},
    "New England Patriots": {"primary": "#002244", "secondary": "#C60C30"},
    "New Orleans Saints": {"primary": "#D3BC8D", "secondary": "#101820"},
    "New York Giants": {"primary": "#0B2265", "secondary": "#A71930"},
    "New York Jets": {"primary": "#125740", "secondary": "#000000"},
    "Philadelphia Eagles": {"primary": "#004C54", "secondary": "#A5ACAF"},
    "Pittsburgh Steelers": {"primary": "#FFB612", "secondary": "#101820"},
    "San Francisco 49ers": {"primary": "#AA0000", "secondary": "#B3995D"},
    "Seattle Seahawks": {"primary": "#002244", "secondary": "#69BE28"},
    "Tampa Bay Buccaneers": {"primary": "#D50A0A", "secondary": "#34302B"},
    "Tennessee Titans": {"primary": "#0C2340", "secondary": "#4B92DB"},
    "Washington Commanders": {"primary": "#5A1414", "secondary": "#FFB612"},

    # NBA
    "Atlanta Hawks": {"primary": "#E03A3E", "secondary": "#C1D32F"},
    "Boston Celtics": {"primary": "#007A33", "secondary": "#BA9653"},
    "Brooklyn Nets": {"primary": "#000000", "secondary": "#FFFFFF"},
    "Charlotte Hornets": {"primary": "#1D1160", "secondary": "#00788C"},
    "Chicago Bulls": {"primary": "#CE1141", "secondary": "#000000"},
    "Cleveland Cavaliers": {"primary": "#6F263D", "secondary": "#FFB81C"},
    "Dallas Mavericks": {"primary": "#00538C", "secondary": "#B8C4CA"},
    "Denver Nuggets": {"primary": "#0E2240", "secondary": "#FEC524"},
    "Detroit Pistons": {"primary": "#C8102E", "secondary": "#1D42BA"},
    "Golden State Warriors": {"primary": "#1D428A", "secondary": "#FFC72C"},
    "Houston Rockets": {"primary": "#CE1141", "secondary": "#000000"},
    "Indiana Pacers": {"primary": "#002D62", "secondary": "#FDBB30"},
    "LA Clippers": {"primary": "#C8102E", "secondary": "#1D428A"},
    "Los Angeles Lakers": {"primary": "#552583", "secondary": "#FDB927"},
    "Memphis Grizzlies": {"primary": "#5D76A9", "secondary": "#12173F"},
    "Miami Heat": {"primary": "#98002E", "secondary": "#F9A01B"},
    "Milwaukee Bucks": {"primary": "#00471B", "secondary": "#EEE1C6"},
    "Minnesota Timberwolves": {"primary": "#0C2340", "secondary": "#236192"},
    "New Orleans Pelicans": {"primary": "#0C2340", "secondary": "#C8102E"},
    "New York Knicks": {"primary": "#F58426", "secondary": "#006BB6"},
    "Oklahoma City Thunder": {"primary": "#007AC1", "secondary": "#EF3B24"},
    "Orlando Magic": {"primary": "#0077C0", "secondary": "#C4CED4"},
    "Philadelphia 76ers": {"primary": "#006BB6", "secondary": "#ED174C"},
    "Phoenix Suns": {"primary": "#1D1160", "secondary": "#E56020"},
    "Portland Trail Blazers": {"primary": "#E03A3E", "secondary": "#000000"},
    "Sacramento Kings": {"primary": "#5A2D81", "secondary": "#63727A"},
    "San Antonio Spurs": {"primary": "#C4CED4", "secondary": "#000000"},
    "Toronto Raptors": {"primary": "#CE1141", "secondary": "#000000"},
    "Utah Jazz": {"primary": "#002B5C", "secondary": "#F9A01B"},
    "Washington Wizards": {"primary": "#002B5C", "secondary": "#E31837"},

    # NHL
    "Anaheim Ducks": {"primary": "#FC4C02", "secondary": "#B5985A"},
    "Arizona Coyotes": {"primary": "#8C2633", "secondary": "#E2D6B5"},
    "Boston Bruins": {"primary": "#FFB81C", "secondary": "#000000"},
    "Buffalo Sabres": {"primary": "#002654", "secondary": "#FDBB2F"},
    "Calgary Flames": {"primary": "#C8102E", "secondary": "#F1BE48"},
    "Carolina Hurricanes": {"primary": "#CC0000", "secondary": "#000000"},
    "Chicago Blackhawks": {"primary": "#CF0A2C", "secondary": "#000000"},
    "Colorado Avalanche": {"primary": "#6F263D", "secondary": "#236192"},
    "Columbus Blue Jackets": {"primary": "#002654", "secondary": "#CE1126"},
    "Dallas Stars": {"primary": "#006847", "secondary": "#8F8F8C"},
    "Detroit Red Wings": {"primary": "#CE1126", "secondary": "#FFFFFF"},
    "Edmonton Oilers": {"primary": "#041E42", "secondary": "#FF4C00"},
    "Florida Panthers": {"primary": "#041E42", "secondary": "#C8102E"},
    "Los Angeles Kings": {"primary": "#111111", "secondary": "#A2AAAD"},
    "Minnesota Wild": {"primary": "#154734", "secondary": "#A6192E"},
    "Montreal Canadiens": {"primary": "#AF1E2D", "secondary": "#192168"},
    "Nashville Predators": {"primary": "#FFB81C", "secondary": "#041E42"},
    "New Jersey Devils": {"primary": "#CE1126", "secondary": "#000000"},
    "New York Islanders": {"primary": "#00539B", "secondary": "#F47D30"},
    "New York Rangers": {"primary": "#0038A8", "secondary": "#CE1126"},
    "Ottawa Senators": {"primary": "#C8102E", "secondary": "#000000"},
    "Philadelphia Flyers": {"primary": "#F74902", "secondary": "#000000"},
    "Pittsburgh Penguins": {"primary": "#FCB514", "secondary": "#000000"},
    "San Jose Sharks": {"primary": "#006D75", "secondary": "#EA7200"},
    "Seattle Kraken": {"primary": "#001628", "secondary": "#99D9D9"},
    "St. Louis Blues": {"primary": "#002F87", "secondary": "#FCB514"},
    "Tampa Bay Lightning": {"primary": "#002868", "secondary": "#FFFFFF"},
    "Toronto Maple Leafs": {"primary": "#00205B", "secondary": "#FFFFFF"},
    "Vancouver Canucks": {"primary": "#00205B", "secondary": "#00843D"},
    "Vegas Golden Knights": {"primary": "#B4975A", "secondary": "#333F42"},
    "Washington Capitals": {"primary": "#041E42", "secondary": "#C8102E"},
    "Winnipeg Jets": {"primary": "#041E42", "secondary": "#AC162C"}
}


score_cache = {}

@st.cache_data(ttl=5)
def get_scores(sport_path, date):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard?dates={date}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        st.error(f"Error fetching scores for {sport_path}: {e}")
        return []

    results = []
    for event in data.get("events", []):
        comp = event['competitions'][0]
        teams = comp['competitors']
        if len(teams) != 2:
            continue

        home = next(t for t in teams if t['homeAway'] == 'home')
        away = next(t for t in teams if t['homeAway'] == 'away')
        situation = comp.get("situation", {})

        results.append({
            "id": event['id'],
            "status": comp['status']['type']['shortDetail'],
            "teams": [
                {
                    "name": away['team']['displayName'],
                    "score": away['score'],
                    "logo": away['team']['logo'],
                    "abbreviation": away['team']['abbreviation'],
                    "possession": away['team']['id'] == situation.get("possession")
                },
                {
                    "name": home['team']['displayName'],
                    "score": home['score'],
                    "logo": home['team']['logo'],
                    "abbreviation": home['team']['abbreviation'],
                    "possession": home['team']['id'] == situation.get("possession")
                }
            ],
            "period": comp['status'].get("period", ""),
            "clock": comp['status'].get("displayClock", ""),
            "on_first": situation.get("onFirst"),
            "on_second": situation.get("onSecond"),
            "on_third": situation.get("onThird"),
            "balls": situation.get("balls"),
            "strikes": situation.get("strikes"),
            "outs": situation.get("outs"),
            "pitcher": situation.get("pitcher", {}).get("athlete", {}).get("displayName"),
            "batter": situation.get("batter", {}).get("athlete", {}).get("displayName"),
            "yard_line": situation.get("yardLine")
        })

    return results

LAST_GOOD_ODDS = {}

@st.cache_data(ttl=86400, show_spinner=False)
def get_odds_data(sport_key):
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds"
    params = {
        "apiKey": ODDS_API_KEY,
        "regions": "us",
        "markets": "spreads,totals,h2h",
        "oddsFormat": "american"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        LAST_GOOD_ODDS[sport_key] = data  # cache successful response
        return data
    except Exception as e:
        st.warning(f"Odds API failed ({e}). Showing last known odds." if sport_key in LAST_GOOD_ODDS else f"Odds API error: {e}")
        return LAST_GOOD_ODDS.get(sport_key, [])

def find_odds_for_game(game, odds_data):
    team_names = [t['name'] for t in game['teams']]
    for entry in odds_data:
        teams = [entry['home_team'], entry['away_team']]
        if all(any(name in team for team in teams) for name in team_names):
            return entry
    return None

def display_odds_for_game(game, sport_key):
    odds_data = get_odds_data(sport_key)
    matched_odds = find_odds_for_game(game, odds_data)

    if matched_odds and matched_odds.get("bookmakers"):
        bookmaker = matched_odds["bookmakers"][0]
        spread = total = moneyline1 = moneyline2 = None
        t1, t2 = game['teams']

        for market in bookmaker.get("markets", []):
            if market["key"] == "spreads":
                for outcome in market["outcomes"]:
                    if outcome["name"] == t1["name"]:
                        spread = f"{outcome['name']} {outcome['point']:+}"
            elif market["key"] == "totals":
                for outcome in market["outcomes"]:
                    total = f"O/U {outcome['point']}"
            elif market["key"] == "h2h":
                for outcome in market["outcomes"]:
                    if outcome["name"] == t1["name"]:
                        moneyline1 = outcome["price"]
                    elif outcome["name"] == t2["name"]:
                        moneyline2 = outcome["price"]

        if spread or total or (moneyline1 and moneyline2):
            st.markdown("### 🧾 Betting Odds")
        if spread:
            st.markdown(f"**Spread:** {spread}")
        if total:
            st.markdown(f"**Total:** {total}")
        if moneyline1 and moneyline2:
            st.markdown(f"**Moneyline:** {t1['name']} ({moneyline1:+}), {t2['name']} ({moneyline2:+})")

# --- FIXED display_scores with formatting fix & score pre-passing ---
def display_scores(sport_name, date, scores):
    sport_cfg = SPORTS[sport_name]

    for game in scores:
        t1, t2 = game['teams']
        game_id = game['id']
        prev = score_cache.get(game_id, (None, None))
        score_cache[game_id] = (t1['score'], t2['score'])

        b1 = prev[0] != t1['score'] and prev[0] is not None
        b2 = prev[1] != t2['score'] and prev[1] is not None

        popup1 = popup2 = ""

        if sport_name in ["NBA (Basketball)", "NFL (Football)", "MLB (Baseball)", "NHL (Hockey)"]:
            try:
                delta1 = int(t1['score']) - int(prev[0]) if prev[0] is not None else 0
                delta2 = int(t2['score']) - int(prev[1]) if prev[1] is not None else 0
                if delta1 > 0:
                    popup1 = f"<div class='scoring-popup'>+{delta1}</div>"
                if delta2 > 0:
                    popup2 = f"<div class='scoring-popup'>+{delta2}</div>"
            except:
                pass

        color1 = TEAM_COLORS.get(t1['name'], {}).get('primary', '#ddd')
        color1b = TEAM_COLORS.get(t1['name'], {}).get('secondary', '#aaa')
        color2 = TEAM_COLORS.get(t2['name'], {}).get('primary', '#ccc')
        color2b = TEAM_COLORS.get(t2['name'], {}).get('secondary', '#bbb')

        score1_class = "team-score-box" + (" score-blink" if b1 else "")
        score2_class = "team-score-box" + (" score-blink" if b2 else "")

        score1_html = (
            f"<div class='team-score-wrapper' style='background: linear-gradient(135deg, {color1}, {color1b})'>"
            f"<div class='team-name'>{t1['name']}</div>{popup1}"
            f"<div class='{score1_class}'>{t1['score']}</div>"
            "</div>"
        )

        score2_html = (
            f"<div class='team-score-wrapper' style='background: linear-gradient(135deg, {color2}, {color2b})'>"
            f"<div class='team-name'>{t2['name']}</div>{popup2}"
            f"<div class='{score2_class}'>{t2['score']}</div>"
            "</div>"
        )

        gradient_style = f"background: linear-gradient(to right, {color1}, {color2});"
        box_style = f"{gradient_style} padding: 1em; border-radius: 12px; box-shadow: 0 0 10px rgba(0,0,0,0.1); margin-bottom: 1em;"

        with st.container():
            st.markdown(f"<div class='score-box' style='{box_style}'>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1, 2, 1])

            with col1:
                st.image(t1['logo'], width=60)
                st.markdown(score1_html, unsafe_allow_html=True)
                if t1['possession']:
                    st.markdown("🏈 Possession")

            with col2:
                st.markdown("### VS")
                st.markdown(f"**{game['status']}**")
                display_odds_for_game(game, sport_cfg['odds_key'])

                if sport_name == "MLB (Baseball)":
                    st.markdown(f"Inning: {game['period']}")
                    diamond_html = f"""
                        <div class="diamond">
                            <div class="base second {'occupied' if game['on_second'] else ''}"></div>
                            <div class="base third {'occupied' if game['on_third'] else ''}"></div>
                            <div class="base first {'occupied' if game['on_first'] else ''}"></div>
                        </div>
                    """
                    st.markdown(diamond_html, unsafe_allow_html=True)
                    st.markdown(f"**Outs:** {game['outs']}")
                    st.markdown(f"**Balls:** {game['balls']}  **Strikes:** {game['strikes']}")
                    if game.get("pitcher"):
                        st.markdown(f"**Pitcher:** {game['pitcher']}")
                    if game.get("batter"):
                        st.markdown(f"**Batter:** {game['batter']}")

                elif sport_name in ["NFL (Football)", "NBA (Basketball)", "NHL (Hockey)"]:
                    st.markdown(f"Period: {game['period']}")
                    st.markdown(f"Clock: {game['clock']}")
                    if sport_name == "NFL (Football)":
                        for team in game['teams']:
                            if team['possession']:
                                yard = game.get("yard_line")
                                if yard:
                                    try:
                                        yard = int(yard)
                                        yard = max(0, min(100, yard))
                                        st.markdown(f"**{team['name']} Offense - Ball on {yard} yard line**")
                                        st.progress(yard / 100)
                                    except:
                                        st.markdown("**Field Position:** Unknown")

            with col3:
                st.image(t2['logo'], width=60)
                st.markdown(score2_html, unsafe_allow_html=True)
                if t2['possession']:
                    st.markdown("🏈 Possession")

            st.markdown("</div>", unsafe_allow_html=True)

# --- Main UI and Sidebar ---

st.sidebar.title("Controls")

if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True

if st.sidebar.button(":arrows_counterclockwise: Refresh Now"):
    st.cache_data.clear()
    st.rerun()

if st.sidebar.button(":pause_button: Toggle Auto-Refresh"):
    st.session_state.auto_refresh = not st.session_state.auto_refresh

st.title(":classical_building: Live Sports Scores Dashboard")
st.markdown("Real-time updates with team logos, stats, and betting odds.")

selected_date = st.sidebar.date_input("Select date:", datetime.today())
formatted_date = selected_date.strftime("%Y%m%d")

for sport_name, sport_cfg in SPORTS.items():
    scores = get_scores(sport_cfg['path'], formatted_date)
    if scores:
        col_logo, col_title = st.columns([1, 5])
        with col_logo:
            st.image(sport_cfg['icon'], width=80, output_format="PNG")
        with col_title:
            st.markdown(f"### {sport_name}")
        display_scores(sport_name, formatted_date, scores)

if st.session_state.auto_refresh:
    time.sleep(2)
    st.cache_data.clear()
    st.rerun()
