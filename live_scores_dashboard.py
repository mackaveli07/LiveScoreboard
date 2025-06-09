import streamlit as st
import requests
from streamlit_extras.let_it_rain import rain
from streamlit_extras.switch_page_button import switch_page
from streamlit_extras.stylable_container import stylable_container
import base64
from PIL import Image
from io import BytesIO
import time

st.set_page_config(page_title="Live Sports Scores", layout="wide")

SPORTS = {
    "NFL (Football)": "football/nfl",
    "NBA (Basketball)": "basketball/nba",
    "MLB (Baseball)": "baseball/mlb",
    "NHL (Hockey)": "hockey/nhl"
}

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
    "Houston Rockets": {"primary": "#CE1141", "secondary": "#C4CED4"},
    "Indiana Pacers": {"primary": "#002D62", "secondary": "#FDBB30"},
    "Los Angeles Clippers": {"primary": "#C8102E", "secondary": "#1D428A"},
    "Los Angeles Lakers": {"primary": "#552583", "secondary": "#FDB927"},
    "Memphis Grizzlies": {"primary": "#5D76A9", "secondary": "#12173F"},
    "Miami Heat": {"primary": "#98002E", "secondary": "#F9A01B"},
    "Milwaukee Bucks": {"primary": "#00471B", "secondary": "#EEE1C6"},
    "Minnesota Timberwolves": {"primary": "#0C2340", "secondary": "#236192"},
    "New Orleans Pelicans": {"primary": "#0C2340", "secondary": "#85714D"},
    "New York Knicks": {"primary": "#006BB6", "secondary": "#F58426"},
    "Oklahoma City Thunder": {"primary": "#007AC1", "secondary": "#EF3B24"},
    "Orlando Magic": {"primary": "#0077C0", "secondary": "#C4CED4"},
    "Philadelphia 76ers": {"primary": "#006BB6", "secondary": "#ED174C"},
    "Phoenix Suns": {"primary": "#1D1160", "secondary": "#E56020"},
    "Portland Trail Blazers": {"primary": "#E03A3E", "secondary": "#000000"},
    "Sacramento Kings": {"primary": "#5A2D81", "secondary": "#63727A"},
    "San Antonio Spurs": {"primary": "#C4CED4", "secondary": "#000000"},
    "Toronto Raptors": {"primary": "#CE1141", "secondary": "#000000"},
    "Utah Jazz": {"primary": "#002B5C", "secondary": "#00471B"},
    "Washington Wizards": {"primary": "#002B5C", "secondary": "#E31837"},
    # NHL
    "Anaheim Ducks": {"primary": "#FC4C02", "secondary": "#B9975B"},
    "Arizona Coyotes": {"primary": "#8C2633", "secondary": "#E2D6B5"},
    "Boston Bruins": {"primary": "#FFB81C", "secondary": "#000000"},
    "Buffalo Sabres": {"primary": "#002654", "secondary": "#FDBB2F"},
    "Calgary Flames": {"primary": "#C8102E", "secondary": "#F1BE48"},
    "Carolina Hurricanes": {"primary": "#CC0000", "secondary": "#000000"},
    "Chicago Blackhawks": {"primary": "#CF0A2C", "secondary": "#000000"},
    "Colorado Avalanche": {"primary": "#6F263D", "secondary": "#236192"},
    "Columbus Blue Jackets": {"primary": "#041E42", "secondary": "#C8102E"},
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
    "Ottawa Senators": {"primary": "#C52032", "secondary": "#000000"},
    "Philadelphia Flyers": {"primary": "#F74902", "secondary": "#000000"},
    "Pittsburgh Penguins": {"primary": "#FCB514", "secondary": "#000000"},
    "San Jose Sharks": {"primary": "#006D75", "secondary": "#EA7200"},
    "Seattle Kraken": {"primary": "#001628", "secondary": "#99D9D9"},
    "St. Louis Blues": {"primary": "#002F87", "secondary": "#FDB827"},
    "Tampa Bay Lightning": {"primary": "#002868", "secondary": "#FFFFFF"},
    "Toronto Maple Leafs": {"primary": "#00205B", "secondary": "#FFFFFF"},
    "Vancouver Canucks": {"primary": "#00205B", "secondary": "#00843D"},
    "Vegas Golden Knights": {"primary": "#B4975A", "secondary": "#333F42"},
    "Washington Capitals": {"primary": "#041E42", "secondary": "#C8102E"},
    "Winnipeg Jets": {"primary": "#041E42", "secondary": "#AC162C"}
}

TEAM_LOGOS = {
    "Philadelphia Eagles": "https://a.espncdn.com/i/teamlogos/nfl/500/phi.png",
    "Dallas Cowboys": "https://a.espncdn.com/i/teamlogos/nfl/500/dal.png",
    "Los Angeles Lakers": "https://a.espncdn.com/i/teamlogos/nba/500/lal.png",
    "Boston Celtics": "https://a.espncdn.com/i/teamlogos/nba/500/bos.png",
    "New York Yankees": "https://a.espncdn.com/i/teamlogos/mlb/500/nyy.png",
    "Los Angeles Dodgers": "https://a.espncdn.com/i/teamlogos/mlb/500/lad.png",
    "Chicago Blackhawks": "https://a.espncdn.com/i/teamlogos/nhl/500/chi.png",
    "Toronto Maple Leafs": "https://a.espncdn.com/i/teamlogos/nhl/500/tor.png",
    # ... add all remaining teams
}

st.sidebar.title("Live Sports Scoreboard")
selected_sport = st.sidebar.selectbox("Select a sport", list(SPORTS.keys()))

sport_path = SPORTS[selected_sport]
sport_league = selected_sport.split()[0]

@st.cache_data(ttl=30)
def get_scores(sport_path):
    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/scoreboard"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

def display_scores(data):
    events = data.get("events", [])
    for event in events:
        competition = event["competitions"][0]
        competitors = competition["competitors"]

        team1 = competitors[0]
        team2 = competitors[1]
        name1 = team1["team"]["displayName"]
        name2 = team2["team"]["displayName"]
        score1 = team1["score"]
        score2 = team2["score"]
        possession = "→" if team1.get("statistics") and team1["statistics"][0].get("abbreviation") == "POS" else ""

        logo1 = TEAM_LOGOS.get(name1, "")
        logo2 = TEAM_LOGOS.get(name2, "")
        colors1 = TEAM_COLORS.get(sport_league, {}).get(name1, ("#FFFFFF", "#000000"))
        colors2 = TEAM_COLORS.get(sport_league, {}).get(name2, ("#FFFFFF", "#000000"))

        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f"<div style='background-color:{colors1[0]}; padding:10px; border-radius:10px;'>"
                        f"<img src='{logo1}' width='50'> <strong>{name1}</strong><br>"
                        f"<h2>{score1}</h2>{possession}</div>", unsafe_allow_html=True)

        with col2:
            st.markdown(f"<div style='background-color:{colors2[0]}; padding:10px; border-radius:10px;'>"
                        f"<img src='{logo2}' width='50'> <strong>{name2}</strong><br>"
                        f"<h2>{score2}</h2></div>", unsafe_allow_html=True)

        st.markdown("---")

score_data = get_scores(sport_path)
if score_data:
    display_scores(score_data)
else:
    st.error("Unable to fetch scores at the moment.")

if st.sidebar.button("Refresh Scores"):
    st.cache_data.clear()
    st.experimental_rerun()
