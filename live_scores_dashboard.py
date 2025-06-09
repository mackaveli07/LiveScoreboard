import streamlit as st
import requests
import time
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="Live Sports Scores", layout="wide")

# Animation and Styling CSS
st.markdown("""
    <style>
    .score-flash {
        animation: blinkFlash 1.5s ease-out;
    }
    @keyframes blinkFlash {
        0% { background-color: var(--flash-color); }
        100% { background-color: transparent; }
    }
    .diamond {
        width: 50px; height: 50px; position: relative; margin: 10px auto;
    }
    .base { width: 12px; height: 12px; background-color: lightgray;
           position: absolute; transform: rotate(45deg); }
    .base.occupied { background-color: green; }
    .first { bottom: 0; right: 0; transform: translate(50%, 50%) rotate(45deg); }
    .second { top: 0; left: 50%; transform: translate(-50%, -50%) rotate(45deg); }
    .third { bottom: 0; left: 0; transform: translate(-50%, 50%) rotate(45deg); }
    </style>
""", unsafe_allow_html=True)

SPORTS = {
    "NFL (Football)": {"path": "football/nfl", "icon": "🏈"},
    "NBA (Basketball)": {"path": "basketball/nba", "icon": "🏀"},
    "MLB (Baseball)": {"path": "baseball/mlb", "icon": "⚾"},
    "NHL (Hockey)": {"path": "hockey/nhl", "icon": "🛂"}
}

# Full 122-team dictionary (example snippet; include all teams)
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

@st.cache_data(ttl=30)
def get_scores(sport_path, date=None):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard"
    if date:
        url += f"?dates={date}"
    try:
        data = requests.get(url).json()
    except Exception as e:
        st.error(f"Error fetching scores: {e}")
        return []
    results = []
    for event in data.get("events", []):
        comp = event['competitions'][0]
        teams = comp['competitors']
        if len(teams) != 2: continue
        home = next(t for t in teams if t['homeAway']=="home")
        away = next(t for t in teams if t['homeAway']=="away")
        sit = comp.get("situation", {})
        results.append({
            "id": event['id'],
            "status": comp['status']['type']['shortDetail'],
            "teams": [
                {"name": away['team']['displayName'], "score": away['score'], "logo": away['team']['logo'], "abbr": away['team']['displayName']},
                {"name": home['team']['displayName'], "score": home['score'], "logo": home['team']['logo'], "abbr": home['team']['displayName']}
            ],
            "on_first": sit.get("onFirst"), "on_second": sit.get("onSecond"), "on_third": sit.get("onThird"),
            "balls": sit.get("balls"), "strikes": sit.get("strikes"), "outs": sit.get("outs"),
            "pitcher": sit.get("pitcher",{}).get("athlete",{}).get("displayName"),
            "batter": sit.get("batter",{}).get("athlete",{}).get("displayName")
        })
    return results

def display_scores(sport, date):
    cfg = SPORTS[sport]
    games = get_scores(cfg["path"], date)
    if not games:
        st.info("No games available.")
        return

    for gm in games:
        t1, t2 = gm["teams"]
        key = gm["id"]
        prev = score_cache.get(key, (None, None))
        score_cache[key] = (t1["score"], t2["score"])
        flash1 = (t1["score"] != prev[0]) and (prev[0] is not None)
        flash2 = (t2["score"] != prev[1]) and (prev[1] is not None)

        sec1 = TEAM_COLORS.get(t1["abbr"], {}).get("secondary", "#ccc")
        sec2 = TEAM_COLORS.get(t2["abbr"], {}).get("secondary", "#ccc")

        def render_score(team, score, flash, sec):
            fl = "score-flash" if flash else ""
            return f"<div class='{fl}' style='--flash-color:{sec}; padding:10px;'><strong>{score}</strong></div>"

        col1, col2, col3 = st.columns([4,2,4])
        with col1:
            st.image(t1["logo"], width=60)
            st.markdown(f"### {t1['name']}")
            st.markdown(render_score(t1, t1["score"], flash1, sec1), unsafe_allow_html=True)
        with col2:
            st.markdown(f"### VS")
            st.markdown(f"**{gm['status']}**")
            if sport!="MLB (Baseball)":
                pass
            else:
                st.markdown(f"Inning: {gm['outs']} | Balls: {gm['balls']} Strikes: {gm['strikes']}")
                if gm["pitcher"]: st.markdown(f"Pitcher: {gm['pitcher']}")
                if gm["batter"]: st.markdown(f"Batter: {gm['batter']}")
        with col3:
            st.image(t2["logo"], width=60)
            st.markdown(f"### {t2['name']}")
            st.markdown(render_score(t2, t2["score"], flash2, sec2), unsafe_allow_html=True)
        st.markdown("---")

# Sidebar & refresh
st.sidebar.title("Controls")
if "auto_refresh" not in st.session_state: st.session_state.auto_refresh=False
if st.sidebar.button("🔁 Refresh Now"):
    st.cache_data.clear(); st.experimental_rerun()
if st.sidebar.button("⏯ Toggle Auto-Refresh"):
    st.session_state.auto_refresh=not st.session_state.auto_refresh

st.title("📻 Live Sports Scores")
sel_date = st.sidebar.date_input("Select date:", datetime.today())
sel_sport = st.sidebar.selectbox("Choose a sport:", list(SPORTS))
display_scores(sel_sport, sel_date.strftime("%Y%m%d"))

if st.session_state.auto_refresh:
    time.sleep(2)
    st.cache_data.clear()
    st.experimental_rerun()
