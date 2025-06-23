from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from datetime import date

def scrape_betiq_odds(league):
    url_map = {
        "mlb": "https://betiq.teamrankings.com/mlb/game-predictions/",
        "nba": "https://betiq.teamrankings.com/nba/game-predictions/",
        "nfl": "https://betiq.teamrankings.com/nfl/game-predictions/",
        "nhl": "https://betiq.teamrankings.com/nhl/game-predictions/",
        "wnba": "https://betiq.teamrankings.com/wnba/game-predictions/"
    }
    url = url_map[league]
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    results = []
    rows = soup.select("table tr")[1:]
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 6:
            continue
        teams = cells[0].text.strip().split(" vs ")
        home = teams[1].strip()
        away = teams[0].strip()
        ml_home = int(cells[1].text.strip())
        ml_away = int(cells[2].text.strip())
        spread = float(cells[3].text.strip().replace("−", "-"))
        total = float(cells[4].text.strip())
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