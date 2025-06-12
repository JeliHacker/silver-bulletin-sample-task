# main.py
# ------------------------------------------------------------
# Compute “wins forfeited to injuries” for every NBA team.
#
#   python main.py                 → prints table
#   python main.py 2025            → pick season (default 2025)
#   python main.py 2025 out.csv    → also write CSV
# ------------------------------------------------------------

import sys
import pandas as pd
import scrape_spotrac_injuries as spotrac
import scrape_bref_ws48        as bref


def wins_lost_pipeline(season: int = 2025) -> pd.DataFrame:
    """Return a DataFrame of wins lost to injury by team."""
    # --- scrape -----------------------------------------------------------
    inj  = spotrac.scrape_spotrac_injuries(season)[["player", "games_missed"]]
    ws48 = bref.scrape_bref_ws48(season)  # one row per stint (NO “TOT” rows)

    # --- 1) compute each stint’s share of the player’s season minutes -----
    totals = ws48.groupby("player", as_index=False)["mp"].sum() \
                 .rename(columns={"mp": "total_mp"})
    ws48 = ws48.merge(totals, on="player", how="left")
    ws48["mp_share"] = ws48["mp"] / ws48["total_mp"]

    # --- 2) left-join injury counts onto the ws48 base --------------------
    df = (
        ws48.merge(inj, on="player", how="left")     # games_missed NaN → no injury
           .fillna({"games_missed": 0})
           .assign(
               games_missed_team=lambda d: d.games_missed * d.mp_share,
               wins_lost=lambda d: (d.war_per_minute * d.mpg * d.games_missed_team)
           )
    )

    # --- 3) aggregate ------------------------------------------------------
    team_losses = (df.groupby("team", as_index=False)["wins_lost"]
                     .sum()
                     .sort_values("wins_lost", ascending=False)
                     .round(2)
                     .reset_index(drop=True))

    return team_losses


if __name__ == "__main__":
    # CLI boilerplate -------------------------------------------------------
    season   = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 2025
    out_path = sys.argv[2] if len(sys.argv) > 2 else None

    losses = wins_lost_pipeline(season)

    if out_path:
        losses.to_csv(out_path, index=False)
        print(f"✓ Wrote results to {out_path} ({len(losses)} teams).")
    else:
        print(f"\nNBA {season} — Wins Lost to Injury\n")
        print(losses.to_string(index=False, formatters={"wins_lost": "{:.2f}".format}))
