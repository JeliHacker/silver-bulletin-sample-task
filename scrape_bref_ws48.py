"""
scrape_bref_ws48.py
————————
Pulls the Advanced box from Basketball-Reference for a given season
(default 2025) and returns a DataFrame with:

    player, team, mp, games, mpg, ws48

The table lives at:
    https://www.basketball-reference.com/leagues/NBA_{YEAR}_advanced.html
and is sometimes wrapped in an HTML comment, so we unwrap comments first.

To generate a .csv file run the following command in your terminal:
    python3 scrape_bref_ws48.py 2025 > player_stats_2024-2025.csv
"""

import re
import sys
import requests
import pandas as pd
from bs4 import BeautifulSoup, Comment
import unicodedata


BREF_URL = "https://www.basketball-reference.com/leagues/NBA_{yr}_advanced.html"
UA_STR = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)


def _ascii(name: str) -> str:
    """Strip accents & keep plain ASCII for join keys."""
    return unicodedata.normalize("NFKD", name) \
                      .encode("ascii", "ignore") \
                      .decode("ascii")


def _extract_table(soup: BeautifulSoup):
    """
    Basketball-Reference sometimes hides the stats table inside an HTML
    comment. Look for it in the main DOM; if not found, scan comments.
    """
    table = soup.find("table", id=re.compile(r"^advanced"))
    if table:
        return table

    # …otherwise search comments
    for c in soup.find_all(string=lambda text: isinstance(text, Comment)):
        if "table" in c:                                # cheap filter
            sub_soup = BeautifulSoup(c, "html.parser")
            table = sub_soup.find("table", id=re.compile(r"^advanced"))
            if table:
                return table
    raise RuntimeError("Advanced stats table not found.")


def scrape_bref_ws48(year: int = 2025) -> pd.DataFrame:
    url = BREF_URL.format(yr=year)
    resp = requests.get(url, headers={"User-Agent": UA_STR}, timeout=20)
    resp.raise_for_status()
    resp.encoding = "utf-8"

    soup = BeautifulSoup(resp.text, "html.parser")
    table = _extract_table(soup)

    records = []
    for tr in table.tbody.find_all("tr"):
        if tr.get("class") == ["thead"]:
            continue                                  # skip header splits

        if "norank" in (tr.get("class") or []):       # skip bottom league average row
            continue

        player_cell = tr.find("td", {"data-stat": "name_display"})
        if not player_cell:                           # separator rows
            continue

        raw_name = player_cell.get_text(strip=True)
        player = _ascii(raw_name)
        team   = tr.find("td", {"data-stat": "team_name_abbr"}).get_text(strip=True)
        if team in ["TOT", "2TM", "3TM"]:
            continue
        games  = int(tr.find("td", {"data-stat": "games"}).get_text(strip=True))
        mp     = int(tr.find("td", {"data-stat": "mp"}).get_text(strip=True))
        ws48_raw = tr.find("td", {"data-stat": "ws_per_48"}).get_text(strip=True)
        ws48 = float(ws48_raw) if ws48_raw != "" else 0.0
        vorp_raw = tr.find("td", {"data-stat": "vorp"}).get_text(strip=True)
        vorp = float(vorp_raw) if vorp_raw != "" else 0.0
        war = vorp * 2.7
        war_per_minute = war / mp

        records.append(
            {
                "player": player,
                "team": team,
                "games": games,
                "mp": mp,
                "ws48": ws48,
                "vorp": vorp,
                "war": war,
                "war_per_minute": war_per_minute
            }
        )

    df = pd.DataFrame.from_records(records)
    df["mpg"] = df["mp"] / df["games"].replace(0, pd.NA)

    return df


if __name__ == "__main__":
    yr = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
    df = scrape_bref_ws48(year=yr)
    df.to_csv(sys.stdout, index=False)
