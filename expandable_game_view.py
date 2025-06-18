
import streamlit as st
import requests

def fetch_team_stats(team_id):
    url = f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/teams/{team_id}"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()

def display_game_details(game):
    with st.expander("More Game Details"):
        sport = game.get("sport", "")
        away = game.get("away_team", {})
        home = game.get("home_team", {})

        st.subheader("Team Info & Odds")

        # Placeholder odds logic (update with real odds fetching logic)
        st.write("🏆 **Odds** (example):")
        st.markdown("- Spread: Home -3.5")
        st.markdown("- Over/Under: 211.5")
        st.markdown("- Moneyline: Home -140 / Away +120")

        if sport == "nba":
            # ESPN team IDs could be mapped or extracted from full API
            away_team_id = get_team_id_from_name(away["name"])
            home_team_id = get_team_id_from_name(home["name"])
            away_stats = fetch_team_stats(away_team_id)
            home_stats = fetch_team_stats(home_team_id)

            if away_stats:
                st.markdown(f"### {away['name']} Player Stats")
                for player in away_stats.get("athletes", []):
                    st.write(f"- **{player.get('displayName', '')}**: {player.get('position', {}).get('abbreviation', '')}")

            if home_stats:
                st.markdown(f"### {home['name']} Player Stats")
                for player in home_stats.get("athletes", []):
                    st.write(f"- **{player.get('displayName', '')}**: {player.get('position', {}).get('abbreviation', '')}")

def get_team_id_from_name(team_name):
    mapping = {
        "Boston Celtics": "2",
        "Los Angeles Lakers": "13",
        "Golden State Warriors": "9",
        # Add more team mappings here
    }
    return mapping.get(team_name, "")
