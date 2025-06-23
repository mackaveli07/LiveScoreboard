import json
import mysql.connector
from elo import update_elo_ratings
from team_mapping import get_team_mapping

def run_elo_pipeline():
    update_elo_ratings()  # assumes elo.py handles updating elo_history.json

def merge_market_with_elo(league, market_games):
    with open("elo_history.json", "r") as f:
        elo_data = json.load(f)
    mapping = get_team_mapping(league)
    merged = []
    for g in market_games:
        home = mapping.get(g["home"], g["home"])
        away = mapping.get(g["away"], g["away"])
        elo_home = elo_data.get(home, 1500)
        elo_away = elo_data.get(away, 1500)
        prob_home = 1 / (1 + 10 ** ((elo_away - elo_home) / 400))
        prob_away = 1 - prob_home
        fair_ml_home = -100 * prob_home / (1 - prob_home) if prob_home >= 0.5 else 100 * (1 - prob_home) / prob_home
        fair_ml_away = -100 * prob_away / (1 - prob_away) if prob_away >= 0.5 else 100 * (1 - prob_away) / prob_away
        edge_home = round(prob_home - g["ml_home_prob"], 4) * 100
        edge_away = round(prob_away - g["ml_away_prob"], 4) * 100
        merged.append({
            "league": league,
            "date": g["date"],
            "home": home,
            "away": away,
            "elo_home": elo_home,
            "elo_away": elo_away,
            "prob_home": round(prob_home, 4),
            "prob_away": round(prob_away, 4),
            "fair_ml_home": round(fair_ml_home),
            "fair_ml_away": round(fair_ml_away),
            "market_ml_home": g["ml_home"],
            "market_ml_away": g["ml_away"],
            "spread": g["spread"],
            "total": g["total"],
            "value_edge_home": edge_home,
            "value_edge_away": edge_away
        })
    return merged

def save_betting_data(league, data):
    conn = mysql.connector.connect(
        host="localhost",
        user="your_user",
        password="your_password",
        database="sports_data"
    )
    cur = conn.cursor()
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS betting_odds (
            id INT AUTO_INCREMENT PRIMARY KEY,
            game_date DATE,
            league VARCHAR(10),
            home_team VARCHAR(20),
            away_team VARCHAR(20),
            elo_home INT,
            elo_away INT,
            market_ml_home INT,
            market_ml_away INT,
            spread FLOAT,
            total FLOAT,
            value_home FLOAT,
            value_away FLOAT
        )
    """)
    for g in data:
        cur.execute(f"""
            INSERT INTO betting_odds
            (game_date, league, home_team, away_team, elo_home, elo_away,
            market_ml_home, market_ml_away, spread, total, value_home, value_away)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            g["date"], g["league"], g["home"], g["away"],
            g["elo_home"], g["elo_away"], g["market_ml_home"], g["market_ml_away"],
            g["spread"], g["total"], g["value_edge_home"], g["value_edge_away"]
        ))
    conn.commit()
    cur.close()
    conn.close()