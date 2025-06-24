import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import psycopg2
import os
from elo_utils import EloRating
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": 5432,
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

def connect_to_db():
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        dbname=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )

LEAGUE_INFO = {
    "NBA": "https://www.basketball-reference.com/leagues/NBA_{}_games.html",
    "WNBA": "https://www.basketball-reference.com/wnba/years/{}_games.html",
    "MLB": "https://www.baseball-reference.com/leagues/MLB/{}-schedule.shtml",
    "NFL": "https://www.pro-football-reference.com/years/{}/games.htm",
    "NHL": "https://www.hockey-reference.com/leagues/NHL_{}_games.html"
}

YEARS = [2022, 2023, 2024]

def fetch_game_data(league, year):
    url = LEAGUE_INFO[league].format(year)
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        return []
    games = []
    table = tables[0]
    rows = table.find("tbody").find_all("tr")
    for row in rows:
        if 'class' in row.attrs and 'thead' in row['class']:
            continue
        cols = row.find_all("td")
        if not cols or len(cols) < 5:
            continue
        try:
            date_str = row.find("th").text.strip()
            date = datetime.strptime(date_str, "%a, %b %d, %Y").date() if league != "NFL" else datetime.strptime(date_str, "%Y-%m-%d").date()
            away_team = cols[0].text.strip()
            home_team = cols[1].text.strip()
            away_score = int(cols[2].text.strip())
            home_score = int(cols[3].text.strip())
            games.append({
                "game_date": date,
                "home_team": home_team,
                "away_team": away_team,
                "home_score": home_score,
                "away_score": away_score
            })
        except Exception:
            continue
    return games

def run_elo(games):
    elo = EloRating()
    rows = []
    for g in sorted(games, key=lambda x: x["game_date"]):
        home = g["home_team"]
        away = g["away_team"]
        home_score = g["home_score"]
        away_score = g["away_score"]
        home_elo_before = elo.get_rating(home)
        away_elo_before = elo.get_rating(away)
        winner = home if home_score > away_score else away
        elo.update_elo(home, away, winner)
        home_elo_after = elo.get_rating(home)
        away_elo_after = elo.get_rating(away)
        rows.append((
            g["game_date"], home, away, home_score, away_score,
            home_elo_before, away_elo_before,
            home_elo_after, away_elo_after
        ))
    return rows

def create_league_table(cursor, table_name):
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id SERIAL PRIMARY KEY,
        game_date DATE,
        home_team TEXT,
        away_team TEXT,
        home_score INT,
        away_score INT,
        home_elo_before FLOAT,
        away_elo_before FLOAT,
        home_elo_after FLOAT,
        away_elo_after FLOAT
    );
    """)

def insert_elo_data(cursor, table_name, rows):
    insert_query = f"""
    INSERT INTO {table_name} (
        game_date, home_team, away_team,
        home_score, away_score,
        home_elo_before, away_elo_before,
        home_elo_after, away_elo_after
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.executemany(insert_query, rows)

def process_league(league):
    print(f"Processing {league}")
    all_games = []
    for year in YEARS:
        all_games += fetch_game_data(league, year)
    return run_elo(all_games)

def main():
    conn = connect_to_db()
    cursor = conn.cursor()
    for league in LEAGUE_INFO:
        table_name = f"elo_{league.lower()}"
        rows = process_league(league)
        create_league_table(cursor, table_name)
        insert_elo_data(cursor, table_name, rows)
        conn.commit()
        print(f"Inserted {len(rows)} rows into {table_name}")
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
