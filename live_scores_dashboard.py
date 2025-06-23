import streamlit as st
import pandas as pd
import json
from elo_utils import run_elo_pipeline, merge_market_with_elo, save_betting_data
from betiq_scraper import scrape_betiq_odds

st.set_page_config(layout="wide")
st.title("🏟️ Cross-League Elo Betting Dashboard")

@st.cache_data(ttl=3600)
def update_all_leagues():
    run_elo_pipeline()
    leagues = ["mlb", "nba", "nfl", "nhl", "wnba"]
    for league in leagues:
        market_odds = scrape_betiq_odds(league)
        merged = merge_market_with_elo(league, market_odds)
        save_betting_data(league, merged)
        with open(f"{league}_predicted_odds.json", "w") as f:
            json.dump(merged, f, indent=2)

if st.button("🔁 Update Elo + BetIQ Odds"):
    update_all_leagues()
    st.success("✅ Data updated!")

tabs = st.tabs(["MLB", "NBA", "NFL", "NHL", "WNBA"])
for i, league in enumerate(["mlb", "nba", "nfl", "nhl", "wnba"]):
    with tabs[i]:
        try:
            with open(f"{league}_predicted_odds.json", "r") as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            df["Value On"] = df.apply(lambda x: "HOME" if x["value_edge_home"] > x["value_edge_away"] else "AWAY", axis=1)
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.warning(f"No data for {league.upper()}: {e}")