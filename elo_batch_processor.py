import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import psycopg2
import os
from elo_utils import EloRating
from dotenv import load_dotenv

load_dotenv()

# Connect to Azure PostgreSQL
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

# Leagues and URL patterns
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
                "league": league,
                "game_date": date,
                "home_team": home_team,
                "away_team": away_team,
                "home_score": home_score,
                "away_score": away_score
            })
        except Exception as e:
            continue
    return games

def run_elo_for_league(league):
    print(f"Processing {league}")
    games = []
    for year in YEARS:
        games += fetch_game_data(league, year)

    # Sort by date
    games = sorted(games, key=lambda x: x["game_date"])

    # Elo processor
    elo = EloRating()
    game_rows = []

    for g in games:
        home = g["home_team"]
        away = g["away_team"]
        home_score = g["home_score"]
        away_score = g["away_score"]

        home_elo = elo.get_rating(home)
        away_elo = elo.get_rating(away)

        if home_score > away_score:
            winner = home
        else:
            winner = away

        elo.update_elo(home, away, winner)

        game_rows.append((
            g["league"],
            g["game_date"],
            home,
            away,
            home_score,
            away_score,
            home_elo,
            away_elo,
            elo.get_rating(home),
            elo.get_rating(away)
        ))

    return game_rows

def write_to_postgres(game_rows):
    conn = connect_to_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS elo_history (
        id SERIAL PRIMARY KEY,
        league TEXT,
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
    conn.commit()

    insert_query = """
    INSERT INTO elo_history (
        league, game_date, home_team, away_team, home_score, away_score,
        home_elo_before, away_elo_before, home_elo_after, away_elo_after
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    cursor.executemany(insert_query, game_rows)
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Inserted {len(game_rows)} rows to Azure DB.")

if __name__ == "__main__":
    all_game_rows = []
    for league in LEAGUE_INFO:
        all_game_rows += run_elo_for_league(league)

    write_to_postgres(all_game_rows)
