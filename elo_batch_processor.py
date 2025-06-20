import csv
import json
from elo import EloRating
from datetime import datetime

def process_elo_from_csv(input_csv_path, league_name, output_json_path=None, output_csv_path=None):
    elo = EloRating()

    with open(input_csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        games = [row for row in reader if row.get("League", "").lower() == league_name.lower()]

    games.sort(key=lambda x: datetime.strptime(x["Date"], "%Y-%m-%d"))

    for game in games:
        home = game["Home Team"].strip()
        away = game["Away Team"].strip()
        try:
            home_score = int(game["Home Score"])
            away_score = int(game["Away Score"])
        except ValueError:
            continue

        result = 1 if home_score > away_score else 0 if home_score < away_score else 0.5
        elo.update_ratings(home, away, result)

    ratings = elo.get_all_ratings()

    if output_json_path:
        with open(output_json_path, "w") as f:
            json.dump(ratings, f, indent=2)

    if output_csv_path:
        with open(output_csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Team", "Elo Rating"])
            for team, rating in ratings.items():
                writer.writerow([team, round(rating, 2)])

    return ratings

if __name__ == "__main__":
    input_csv = "historical_mlb_games_3seasons.csv"
    league = "mlb"
    json_out = "mlb_elo_ratings.json"
    csv_out = "mlb_elo_ratings.csv"

    ratings = process_elo_from_csv(input_csv, league, json_out, csv_out)

    print("Top 10 Elo Ratings:")
    for team, rating in sorted(ratings.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{team}: {round(rating)}")
