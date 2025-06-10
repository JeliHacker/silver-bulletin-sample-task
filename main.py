# main.py
# ------------------------------------------------------------
# Pull Spotrac injury data + B-Ref WS/48 data, merge, and
# compute “wins forfeited to injuries” for every NBA team.
#
# USAGE
#   python main.py                # prints table to stdout
#   python main.py 2025           # pick season (defaults 2025)
#   python main.py 2025 team_loss.csv   # also write CSV
# ------------------------------------------------------------

import sys
import pandas as pd

import scrape_spotrac_injuries as spotrac
import scrape_bref_ws48        as bref


def wins_lost_pipeline(season: int = 2025) -> pd.DataFrame:
    """Return a DataFrame of wins lost to injury by team."""

    inj  = spotrac.scrape_spotrac_injuries(season)
    ws48 = bref.scrape_bref_ws48(season)
    print("inj columns:", inj.columns)
    print("ws48 columns:", ws48.columns)

    # Merge on player name (case-sensitive, both scrapers strip() names)
    df = (
        inj.merge(
            ws48[["player", "team", "mpg", "ws48"]],
            on="player",
            how="left",
            suffixes=("", "_bref")
            )
           .dropna(subset=["ws48", "mpg"])          # players w/o stats → skip
           .assign(
               wins_lost=lambda d: d.ws48 * d.mpg * d.games_missed / 48
           )
    )

    print("okc df:")
    okc_df = df[df['team'] == "OKC"].sort_values("wins_lost")
    with pd.option_context('display.max_columns', None):
        print(okc_df)

    team_losses = (
        df.groupby("team", as_index=False)["wins_lost"]
          .sum()
          .sort_values("wins_lost", ascending=False)
          .reset_index(drop=True)
    )

    return team_losses


if __name__ == "__main__":
    # ------------- CLI boilerplate --------------------------
    season   = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 2025
    out_path = sys.argv[2] if len(sys.argv) > 2 else None
    # --------------------------------------------------------

    losses = wins_lost_pipeline(season)

    if out_path:
        losses.to_csv(out_path, index=False)
        print(f"✓ Wrote results to {out_path} ({len(losses)} teams).")
    else:
        # Pretty-print to console
        print(f"\nNBA {season}  —  Wins Lost to Injury\n")
        print(losses.to_string(index=False, formatters={"wins_lost": "{:.2f}".format}))
