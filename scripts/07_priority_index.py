#!/usr/bin/env python3
"""
07_priority_index.py — Calculate intervention priority indices and classify.

OHSPI = HRI_norm − OHSI   (outdoor heat shelter priority)
IHSPI = HRI_norm − IHSI   (indoor heat shelter priority)

Positive values -> high risk + low shelter -> needs intervention.
Negative values -> risk adequately covered by existing shelters.
Range is approximately [−0.8, +0.8].

Priority categories (OHSPI_CAT / IHSPI_CAT):
  Adequate : value < 0      (shelter supply exceeds local heat risk)
  Low      : 0.0 ≤ value < 0.1
  Medium   : 0.1 ≤ value < 0.3
  High     : value ≥ 0.3

Also applies 7-class Natural Breaks (Jenks) to HRI for continuous visualization.
"""

import sys
from pathlib import Path

import geopandas as gpd
import mapclassify
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import BLOCKS_URBAN_FILE, JENKS_CLASSES


def classify_jenks(series: pd.Series, k: int = JENKS_CLASSES) -> np.ndarray:
    """Apply Natural Breaks classification, return class labels 1..k."""
    values = series.dropna().values
    n_unique = len(np.unique(values))
    if n_unique < k:
        k = max(2, n_unique)
    classifier = mapclassify.NaturalBreaks(values, k=k)
    labels = np.full(len(series), np.nan)
    mask = series.notna()
    labels[mask] = classifier.yb + 1  # 1-based
    return labels.astype(int)


def priority_category(series: pd.Series) -> pd.Series:
    """Map priority index values to 4-tier intervention category.

    Thresholds are policy-defined: a value of exactly 0 means shelter supply
    equals local heat risk, which we classify as 'Adequate' (the left-open
    convention in pd.cut: (−∞, 0] → Adequate).
    """
    cats = pd.cut(
        series,
        bins=[-np.inf, 0, 0.1, 0.3, np.inf],
        labels=["Adequate", "Low", "Medium", "High"],
    )
    return cats


def main():
    print("=" * 60)
    print("STEP 7: Priority Indices")
    print("=" * 60)

    blocks = gpd.read_file(BLOCKS_URBAN_FILE)
    print(f"\n  Loaded {len(blocks)} urban inhabited blocks")

    # -- Priority indices -----------------------------------------------
    print("\n[1/3] Computing OHSPI and IHSPI ...")
    blocks["ohspi"] = blocks["hri_norm"] - blocks["ohsi"]
    blocks["ihspi"] = blocks["hri_norm"] - blocks["ihsi"]

    print(f"  OHSPI: [{blocks['ohspi'].min():.3f}, {blocks['ohspi'].max():.3f}]")
    print(f"  IHSPI: [{blocks['ihspi'].min():.3f}, {blocks['ihspi'].max():.3f}]")

    # -- Priority categories -------------------------------------------
    print("\n[2/3] Assigning priority categories ...")
    blocks["ohspi_cat"] = priority_category(blocks["ohspi"])
    blocks["ihspi_cat"] = priority_category(blocks["ihspi"])

    for col in ["ohspi_cat", "ihspi_cat"]:
        vc = blocks[col].value_counts().reindex(["Adequate", "Low", "Medium", "High"], fill_value=0)
        total = len(blocks)
        print(f"  {col}: " + ", ".join(f"{cat}={n} ({n/total*100:.1f}%)" for cat, n in vc.items()))

    # -- Jenks classification for HRI (continuous variable) -----------
    print(f"\n[3/3] Jenks {JENKS_CLASSES}-class classification for HRI ...")
    blocks["hri_class"] = classify_jenks(blocks["hri_norm"])
    print(f"  hri_class: {dict(blocks['hri_class'].value_counts().sort_index())}")

    # Save
    blocks.to_file(BLOCKS_URBAN_FILE, driver="GPKG")
    print(f"\n  [OK] Saved with priority indices -> {BLOCKS_URBAN_FILE}")

    print("\n" + "=" * 60)
    print("Priority index calculation complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
