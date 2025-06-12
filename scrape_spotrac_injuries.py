"""
scrape_spotrac_injuries.py
———————————
Quick-n-dirty Spotrac NBA injury tracker scraper.

•  Defaults to the current season (2025) and the “player” view, e.g.
  https://www.spotrac.com/nba/injured/_/year/2025/view/player
•  Returns a pandas DataFrame with:
     rank, player, pos, team, injury_details,
     games_missed, days_missed, cash_total

Run it from the CLI:

    python scrape_spotrac_injuries.py 2024 > injuries_2024-2025.csv
"""

import re
import sys
import requests
import pandas as pd
from bs4 import BeautifulSoup


def scrape_spotrac_injuries(year: int = 2025,
                            view: str = "player") -> pd.DataFrame:
    url = f"https://www.spotrac.com/nba/injured/_/year/{year}/view/{view}"
    headers = {
        # A UA string helps avoid 403s
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        )
    }

    resp = requests.get(url, headers=headers, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.select("table tbody tr")

    records = []
    for tr in rows:
        tds = tr.find_all("td")
        if len(tds) < 8:          # header rows / ads → skip
            continue
        try:
            rank = int(tds[0].get_text(strip=True))
        except ValueError:        # “Rank” col will be non-numeric in header rows
            continue

        player = tds[1].get_text(strip=True)
        pos    = tds[2].get_text(strip=True)

        # cell 3 contains an <img> + “NOP” etc.  Grab only the abbrev.
        team_txt = "".join(tds[3].stripped_strings)
        team_abbr = re.search(r"[A-Z]{2,3}$", team_txt).group(0)

        injury_details = " | ".join(
            div.get_text(" ", strip=True) for div in tds[4].find_all("div")
        )

        games_missed = int(tds[5].get_text(strip=True).replace(",", ""))
        days_missed  = int(tds[6].get_text(strip=True).replace(",", ""))

        cash_total = (
            tds[7]
            .get_text(strip=True)
            .replace("$", "")
            .replace(",", "")
        )
        cash_total = int(cash_total)

        records.append(
            {
                "rank": rank,
                "player": player,
                "pos": pos,
                "team": team_abbr,
                "injury_details": injury_details,
                "games_missed": games_missed,
                "days_missed": days_missed,
                "cash_total": cash_total,
            }
        )

    return pd.DataFrame.from_records(records)


if __name__ == "__main__":
    yr = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
    df = scrape_spotrac_injuries(year=yr)
    df.to_csv(sys.stdout, index=False)
