import streamlit as st
import requests
import time
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="Live Sports Scores", layout="wide")

# Animation and Style CSS
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&family=Oswald:wght@400;700&display=swap');

    .blinking {
        animation: blinker 1s linear infinite;
    }
    @keyframes blinker {
        50% { opacity: 0.5; }
    }
    .diamond {
        width: 50px;
        height: 50px;
        position: relative;
        margin: 10px auto;
    }
    .base {
        width: 12px;
        height: 12px;
        background-color: lightgray;
        position: absolute;
        transform: rotate(45deg);
    }
    .base.occupied {
        background-color: green;
    }
    .first { bottom: 0; right: 0; transform: translate(50%, 50%) rotate(45deg); }
    .second { top: 0; left: 50%; transform: translate(-50%, -50%) rotate(45deg); }
    .third { bottom: 0; left: 0; transform: translate(-50%, 50%) rotate(45deg); }
    .scoring-indicator {
        animation: flash 1s infinite;
        font-weight: bold;
        padding: 0.25em 0.5em;
        border-radius: 5px;
        display: inline-block;
    }
    @keyframes flash {
        0% { opacity: 1; }
        50% { opacity: 0.2; }
        100% { opacity: 1; }
    }
    .score-blink {
        animation: blinkScore 1s step-start 0s infinite;
    }
    @keyframes blinkScore {
        0% { opacity: 1; }
        50% { opacity: 0; }
        100% { opacity: 1; }
    }
    .team-font-NFL { font-family: 'Roboto', sans-serif; }
    .team-font-NBA { font-family: 'Oswald', sans-serif; }
    .team-font-MLB { font-family: 'Roboto', sans-serif; }
    .team-font-NHL { font-family: 'Oswald', sans-serif; }
    </style>
""", unsafe_allow_html=True)

SPORTS = {
    "NFL (Football)": {"path": "football/nfl", "icon": "🏈", "font_class": "team-font-NFL"},
    "NBA (Basketball)": {"path": "basketball/nba", "icon": "🏀", "font_class": "team-font-NBA"},
    "MLB (Baseball)": {"path": "baseball/mlb", "icon": "⚾", "font_class": "team-font-MLB"},
    "NHL (Hockey)": {"path": "hockey/nhl", "icon": "🚂", "font_class": "team-font-NHL"}
}

def display_scores(sport_name, date):
    sport_config = SPORTS[sport_name]
    font_class = sport_config.get("font_class", "")
    st.markdown(f"## <span class='{font_class}'>{sport_config['icon']} {sport_name}</span>", unsafe_allow_html=True)

    # Example usage of font_class within team name display (simplified example)
    st.markdown(f"<p class='{font_class}'>Live Scores for {sport_name} on {date}</p>", unsafe_allow_html=True)

    # Placeholder for game rendering logic
    st.markdown("Games would be displayed here...")
