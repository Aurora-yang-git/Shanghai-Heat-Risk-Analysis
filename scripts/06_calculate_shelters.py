#!/usr/bin/env python3
"""
06_calculate_shelters.py — Calculate heat shelter indices.

OHSI (Outdoor Heat Shelter Index):
  OHSI = rank_normalize(green_area_m2 / pop_sum)

IHSI (Indoor Heat Shelter Index):
  IHSI = rank_normalize((poi_density / pop_density) × mean_wt)

Rank normalization maps percentile rank to [NORM_MIN, NORM_MAX]. This reveals
relative spatial differentiation across urban blocks — blocks with zero shelter
all receive NORM_MIN (tied at the bottom); the best-served block receives NORM_MAX.
"""

import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import BLOCKS_URBAN_FILE, NORM_MAX, NORM_MIN


def rank_normalize(series: pd.Series) -> pd.Series:
    """Rank-normalize to [NORM_MIN, NORM_MAX].

    Ties use method='min' so all blocks with zero shelter receive the same
    lowest score. Guards against an all-zero series (returns NORM_MIN).
    """
    if series.max() == 0:
        return pd.Series(NORM_MIN, index=series.index)
    ranked = series.rank(pct=True, method="min")
    return NORM_MIN + (NORM_MAX - NORM_MIN) * ranked


def main():
    print("=" * 60)
    print("STEP 6: Calculate Shelter Indices")
    print("=" * 60)

    blocks = gpd.read_file(BLOCKS_URBAN_FILE)
    print(f"\n  Loaded {len(blocks)} urban inhabited blocks")

    # -- OHSI -----------------------------------------------------------
    print("\n[1/2] OHSI = rank_normalize(green_area / population) ...")
    gspc = blocks["green_area_m2"] / blocks["pop_sum"].clip(lower=1)
    blocks["ohsi"] = rank_normalize(gspc)
    print(f"  Green space per capita: [{gspc.min():.2f}, {gspc.max():.2f}] m²/person")
    pct_zero = (gspc == 0).mean() * 100
    print(f"  Blocks with zero green space: {pct_zero:.1f}%")
    print(f"  OHSI (rank-normalized): [{blocks['ohsi'].min():.3f}, {blocks['ohsi'].max():.3f}]")

    # -- IHSI -----------------------------------------------------------
    print("\n[2/2] IHSI = rank_normalize((poi_density / pop_density) × mean_wt) ...")
    ihsi_raw = (
        blocks["poi_density"]
        / blocks["pop_density"].clip(lower=0.001)
        * blocks["mean_wt"]
    )
    ihsi_raw = ihsi_raw.fillna(0)  # blocks with no POIs get NaN from mean_wt=NaN
    blocks["ihsi"] = rank_normalize(ihsi_raw)
    print(f"  IHSI raw: [{ihsi_raw.min():.4f}, {ihsi_raw.max():.4f}]")
    pct_zero_ihsi = (ihsi_raw == 0).mean() * 100
    print(f"  Blocks with no indoor shelter POIs: {pct_zero_ihsi:.1f}%")
    print(f"  IHSI (rank-normalized): [{blocks['ihsi'].min():.3f}, {blocks['ihsi'].max():.3f}]")

    # Save
    blocks.to_file(BLOCKS_URBAN_FILE, driver="GPKG")
    print(f"\n  [OK] Saved with shelter indices -> {BLOCKS_URBAN_FILE}")

    print("\n" + "=" * 60)
    print("Shelter indices complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
