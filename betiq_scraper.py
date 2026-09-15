from datetime import date

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

FETCH_TIMEOUT = 20
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
}


def _fetch_page_source(url):
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=FETCH_TIMEOUT)
        response.raise_for_status()
        if "<table" in response.text.lower():
            return response.text
    except requests.RequestException:
        pass

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)
    try:
        driver.get(url)
        return driver.page_source
    finally:
        driver.quit()


def _parse_matchup(matchup_text):
    cleaned = " ".join(matchup_text.split())
    separators = (" vs ", " @ ", " at ")

    for separator in separators:
        if separator in cleaned:
            away, home = cleaned.split(separator, 1)
            return away.strip(), home.strip()

    raise ValueError(f"Unsupported matchup format: {matchup_text}")


def _parse_moneyline(value):
    return int(value.strip().replace("−", "-").replace("+", ""))


def _parse_number(value):
    return float(value.strip().replace("−", "-"))

def scrape_betiq_odds(league):
    url_map = {
        "mlb": "https://betiq.teamrankings.com/mlb/game-predictions/",
        "nba": "https://betiq.teamrankings.com/nba/game-predictions/",
        "nfl": "https://betiq.teamrankings.com/nfl/game-predictions/",
        "nhl": "https://betiq.teamrankings.com/nhl/game-predictions/",
        "wnba": "https://betiq.teamrankings.com/wnba/game-predictions/"
    }
    url = url_map[league]
    soup = BeautifulSoup(_fetch_page_source(url), "html.parser")

    results = []
    rows = soup.select("table tr")[1:]
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 6:
            continue
        away, home = _parse_matchup(cells[0].get_text(" ", strip=True))
        ml_home = _parse_moneyline(cells[1].get_text(strip=True))
        ml_away = _parse_moneyline(cells[2].get_text(strip=True))
        spread = _parse_number(cells[3].get_text(strip=True))
        total = _parse_number(cells[4].get_text(strip=True))
        prob_home = 100 / (abs(ml_home) + 100) if ml_home > 0 else abs(ml_home) / (abs(ml_home) + 100)
        prob_away = 100 / (abs(ml_away) + 100) if ml_away > 0 else abs(ml_away) / (abs(ml_away) + 100)
        results.append({
            "date": str(date.today()),
            "home": home,
            "away": away,
            "ml_home": ml_home,
            "ml_away": ml_away,
            "spread": spread,
            "total": total,
            "ml_home_prob": round(prob_home, 4),
            "ml_away_prob": round(prob_away, 4)
        })
    return results