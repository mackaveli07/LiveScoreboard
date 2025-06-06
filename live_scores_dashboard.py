# New additions at the top
from datetime import timedelta

# Add this below SPORT and TEAM_COLORS dictionaries
def get_team_schedule(team_abbr, sport_path):
    cache_key = f"schedule-{sport_path}-{team_abbr}"
    if cache_key in st.session_state.schedule_cache:
        return st.session_state.schedule_cache[cache_key]

    url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_path}/teams/{team_abbr}/schedule"
    try:
        response = requests.get(url)
        data = response.json()
    except Exception as e:
        st.error(f"Error fetching team schedule: {e}")
        return []

    games = []
    for event in data.get("events", []):
        comp = event['competitions'][0]
        opponent = comp['competitors'][1] if comp['competitors'][0]['team']['abbreviation'] == team_abbr else comp['competitors'][0]
        is_home = comp['competitors'][0]['team']['abbreviation'] == team_abbr
        games.append({
            "date": event.get("date", ""),
            "opponent": opponent['team']['displayName'],
            "opponent_logo": opponent['team']['logo'],
            "home": is_home,
            "status": comp['status']['type']['shortDetail'],
            "score": f"{comp['competitors'][0]['score']} - {comp['competitors'][1]['score']}"
        })

    st.session_state.schedule_cache[cache_key] = games
    return games

# Replace this block near the bottom under Main content section
team_options = {}
for sport_name, sport_data in SPORTS.items():
    try:
        teams_url = f"https://site.api.espn.com/apis/site/v2/sports/{sport_data['path']}/teams"
        resp = requests.get(teams_url)
        data = resp.json()
        for item in data.get("sports", [])[0].get("leagues", [])[0].get("teams", []):
            team = item['team']
            team_options[f"{team['displayName']} ({sport_name})"] = (team['abbreviation'], sport_data['path'])
    except:
        continue

selected_team_key = st.sidebar.selectbox("📅 View Team Schedule", ["None"] + list(team_options.keys()))

if selected_team_key != "None":
    team_abbr, sport_path = team_options[selected_team_key]
    st.subheader(f"🗓 Schedule for {selected_team_key}")
    schedule = get_team_schedule(team_abbr, sport_path)
    for game in schedule:
        col1, col2, col3 = st.columns([1, 3, 3])
        with col1:
            st.image(game['opponent_logo'], width=40)
        with col2:
            st.markdown(f"**vs {'@' if not game['home'] else ''}{game['opponent']}**")
            st.markdown(f"🕒 {datetime.strptime(game['date'], '%Y-%m-%dT%H:%MZ').strftime('%b %d, %Y')}")
        with col3:
            st.markdown(f"{game['status']} — {game['score']}")
    st.stop()  # Stop further rendering of live scores when viewing schedule
