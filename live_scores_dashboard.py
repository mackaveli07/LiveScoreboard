import streamlit as st
import requests
import time
from datetime import datetime

st.set_page_config(page_title="Live Sports Scores", layout="wide")

# CSS styles for animations and diamond
st.markdown("""
    <style>
    .blinking {
        animation: blinker 1s linear infinite;
    }
    @keyframes blinker {
        50% { opacity: 0.5; }
    }
    @keyframes flash {
        0% { background-color: white; color: black; }
        50% { background-color: black; color: white; }
        100% { background-color: white; color: black; }
    }
    .score-box {
        padding: 8px 12px;
        border-radius: 10px;
        font-weight: bold;
        font-size: 24px;
        display: inline-block;
        min-width: 60px;
        text-align: center;
        margin-top: 4px;
    }
    .flash {
        animation: flash 1s infinite;
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
    .score-container {
        background: linear-gradient(to right, var(--t1-color), var(--t2-color));
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 20px;
        border: 3px solid #ccc;
    }
    .score-gradient-box {
        background: linear-gradient(to right, var(--t1-color), var(--t2-color));
        border: 2px solid #000;
        border-radius: 15px;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ... rest of the code remains unchanged until display_scores

# Replace the score1_html and score2_html and container
        score1_html = f"<div class='score-box {'flash' if t1_changed else ''}' style='color:white'>{t1['score']}</div>"
        score2_html = f"<div class='score-box {'flash' if t2_changed else ''}' style='color:white'>{t2['score']}</div>"

        st.markdown(
            f"""
            <div class='score-gradient-box' style="--t1-color: {t1_color}; --t2-color: {t2_color};">
            """,
            unsafe_allow_html=True
        )

# The rest of the display_scores function and app logic remains unchanged
