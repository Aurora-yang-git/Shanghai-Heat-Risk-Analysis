#!/usr/bin/env python3
"""
10_infographic.py -- Shanghai HRI Pipeline Process Infographic

Outputs:
  Composite figures (PPT-ready):
    map_process_hri.png       -- flow strip + 4 HRI component maps
    map_process_shelter.png   -- 3 shelter maps + key-numbers card

  Individual map PNGs (for custom layout):
    map_process_hazard.png
    map_process_exposure.png
    map_process_vulnerability.png
    map_process_hri_solo.png
    map_process_green.png
    map_process_ohsi.png
    map_process_ihsi.png
"""

import sys
import warnings
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from matplotlib.colors import LinearSegmentedColormap

from config import BLOCKS_FILE, MAPS_DIR, PROCESSED_DIR

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------

C = {
    "box_input":     "#EEEEEE",
    "box_norm":      "#D6EAF8",
    "box_hri":       "#FDEBD0",
    "box_shelter_in": "#D5F5E3",
    "box_shelter_idx": "#A9DFBF",
    "arrow":         "#999999",
    "card_bg":       "#F5F5F5",
    "red":           "#C0392B",
    "orange":        "#E8631A",
    "gray":          "#666666",
    "dark":          "#222222",
}

# Green→red ramp without the pale cream centre of RdYlGn — mid-ranked blocks
# stay visibly coloured instead of reading as blank white.
PRIORITY_RAMP = LinearSegmentedColormap.from_list(
    "priority",
    ["#1a9850", "#66bd63", "#a6d96a", "#d9ef8b",
     "#fee08b", "#fdae61", "#f46d43", "#d73027", "#a50026"],
)

_SILHOUETTE_CACHE = {}


def land_silhouette(gdf_all):
    """Land outline built from road blocks via morphological closing.

    shanghai_boundary.gpkg is only the rectangular study frame, so the road
    tessellation is the best available land mask: buffer out 1.5 km, union,
    buffer back — internal holes seal shut, the sea stays outside.
    """
    if "sil" not in _SILHOUETTE_CACHE:
        roads = gdf_all[gdf_all["block_type"] == "road"]
        closed = (roads.geometry.simplify(50)
                  .buffer(1500).union_all().buffer(-1500))
        _SILHOUETTE_CACHE["sil"] = closed
    return _SILHOUETTE_CACHE["sil"]


# Map panel specs: (column, cmap, vmin, vmax_mode, title, subtitle)
# vmax_mode: float = fixed vmax; "p97" = 97th percentile; "p95" = 95th percentile
PANEL_SPECS = {
    "hazard": (
        "hazard", "YlOrRd", 0.1, 0.9,
        "① Heat Hazard", "Normalized UTCI heat stress",
        "Score (0.1–0.9)",
    ),
    "exposure": (
        "exposure", "Blues", 0.1, "p97",
        "② Population Exposure", "Normalized population density",
        "Score",
    ),
    "vulnerability": (
        "vulnerability", "Purples", 0.1, 0.9,
        "③ Economic Vulnerability", "Inverse wealth (nightlight + GDP)",
        "Score (0.1–0.9)",
    ),
    "hri": (
        "hri_norm", "Reds", 0.10, 0.50,
        "= Heat Risk Index (HRI)", "① × ② × ③, normalized",
        "HRI score",
    ),
    "green": (
        "log_green", "YlGn", 0.0, "p95",
        "④ Green Space Area", "log(m²/block) — 89% of blocks = 0",
        "log(m²)",
    ),
    "ohsi": (
        "ohsi", "YlGn", 0.1, 0.9,
        "⑤ Outdoor Shelter Supply (OHSI)", "Green space per capita",
        "OHSI score",
    ),
    "ihsi": (
        "ihsi", "YlGn", 0.1, 0.9,
        "⑥ Indoor Cooling Facilities (IHSI)", "Weighted POI density per capita",
        "IHSI score",
    ),
    # Priority maps: percentile-rank coloring. The raw index is hyper-
    # concentrated (p25–p75 ≈ 0.040–0.046), so a linear scale renders one
    # orange blob; ranking spreads the full green→red ramp evenly.
    "ohspi": (
        "ohspi", PRIORITY_RAMP, "rank", None,
        "⑦ Outdoor Priority (OHSPI)", "red = high risk, low green space",
        "OHSPI percentile — relative priority",
    ),
    "ihspi": (
        "ihspi", PRIORITY_RAMP, "rank", None,
        "⑧ Indoor Priority (IHSPI)", "red = high risk, few indoor cooling facilities",
        "IHSPI percentile — relative priority",
    ),
}


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def load_data():
    print("Loading road blocks ...")
    gdf_all = gpd.read_file(BLOCKS_FILE)
    gdf = gdf_all[gdf_all["block_type"] == "road"].copy()
    gdf["log_green"] = np.log1p(gdf["green_area_m2"])
    print(f"  {len(gdf):,} road blocks")
    return gdf_all, gdf


def resolve_vmax(gdf, column, vmax_spec):
    if isinstance(vmax_spec, str):
        p = int(vmax_spec[1:])
        return float(gdf[column].quantile(p / 100))
    return vmax_spec


# ---------------------------------------------------------------------------
# Shared render
# ---------------------------------------------------------------------------

def render_map(ax, gdf, gdf_all, key, legend=True):
    col, cmap, vmin, vmax_spec, title, subtitle, leg_label = PANEL_SPECS[key]
    draw_boundary = False
    if vmin == "rank":
        # Full-coverage variant: colour EVERY block (road + grid) whose
        # representative point falls inside the land silhouette, so the
        # land area has no gray holes; the sea keeps the gray frame.
        draw_boundary = True
        sil = land_silhouette(gdf_all)
        inside = gdf_all.representative_point().within(sil)
        gdf = gdf_all.loc[inside, [col, "geometry"]].copy()
        gdf["_rank"] = gdf[col].rank(pct=True) * 100
        col = "_rank"
        vmin, vmax = 0.0, 100.0
    else:
        vmax = resolve_vmax(gdf, col, vmax_spec)
        if vmin == "sym":
            vmin = -vmax

    gdf_all.plot(ax=ax, color="#E0E0E0", edgecolor="none", linewidth=0)
    gdf.plot(
        column=col, ax=ax, cmap=cmap,
        vmin=vmin, vmax=vmax,
        linewidth=0, antialiased=False,
        legend=legend,
        legend_kwds={
            "shrink": 0.55,
            "orientation": "horizontal",
            "pad": 0.02,
            "label": leg_label,
        } if legend else {},
    )
    if draw_boundary:
        gpd.GeoSeries([land_silhouette(gdf_all)], crs=gdf_all.crs).boundary.plot(
            ax=ax, color="#999999", linewidth=0.4)
    ax.set_axis_off()
    ax.set_title(title, fontsize=10, fontweight="bold",
                 color=C["dark"], pad=3, loc="center")
    if subtitle:
        ax.text(0.5, -0.01, subtitle, transform=ax.transAxes,
                ha="center", va="top", fontsize=7.5,
                color=C["gray"], style="italic")


# ---------------------------------------------------------------------------
# Flow strip
# ---------------------------------------------------------------------------

def draw_flow_strip(ax):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.5, 0.97, "Shanghai Heat Risk Framework — How We Built It",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=13, fontweight="bold", color=C["dark"])

    boxes = [
        (0.04,  "Raw Data\nUTCI · Population\nNightlight · GDP",  C["box_input"]),
        (0.24,  "Normalize\nto [0.1, 0.9]\nper variable",         C["box_norm"]),
        (0.44,  "HRI  =  Hazard\n× Exposure\n× Vulnerability",    C["box_hri"]),
        (0.64,  "Shelter Resources\nGreen Space\n+ POI Facilities",C["box_shelter_in"]),
        (0.84,  "Shelter Supply\nIndices\nOHSI · IHSI",            C["box_shelter_idx"]),
    ]
    bw, bh, by = 0.16, 0.72, 0.10
    tr = ax.transAxes

    for x0, label, color in boxes:
        ax.add_patch(FancyBboxPatch(
            (x0, by), bw, bh,
            boxstyle="round,pad=0.01",
            facecolor=color, edgecolor="#BBBBBB", linewidth=0.8,
            transform=tr, clip_on=False,
        ))
        ax.text(x0 + bw / 2, by + bh / 2, label,
                transform=tr, ha="center", va="center",
                fontsize=8, color=C["dark"], multialignment="center")

    for x in [0.20, 0.40, 0.60, 0.80]:
        ax.annotate(
            "", xy=(x + 0.04, by + bh / 2),
            xytext=(x, by + bh / 2),
            xycoords=tr, textcoords=tr,
            arrowprops=dict(arrowstyle="->", color=C["arrow"],
                            lw=1.4, mutation_scale=13),
        )

    ax.text(0.995, 0.02,
            "▶  Priority maps (OHSPI / IHSPI) on next slide",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=7, color=C["gray"], style="italic")


# ---------------------------------------------------------------------------
# Annotation card
# ---------------------------------------------------------------------------

def draw_card(ax, gdf):
    ax.set_axis_off()
    ax.set_facecolor(C["card_bg"])

    pct_no_green = (gdf["green_area_m2"] == 0).sum() / len(gdf) * 100
    pct_no_poi   = (gdf["weighted_poi_count"] == 0).sum() / len(gdf) * 100
    n_high_hri   = (gdf["hri_class"] >= 4).sum()

    entries = [
        (0.50, 0.88, f"{pct_no_green:.0f}%",  19, "bold",   C["red"]),
        (0.50, 0.74, "of blocks have no\nmapped green space", 8, "normal", C["dark"]),
        (0.50, 0.58, f"{pct_no_poi:.0f}%",    19, "bold",   C["red"]),
        (0.50, 0.44, "have no cooling\nPOIs within the block", 8, "normal", C["dark"]),
        (0.50, 0.28, f"{n_high_hri:,}",       19, "bold",   C["orange"]),
        (0.50, 0.13, "blocks classified as\nhigh heat risk (class ≥ 4/7)", 8, "normal", C["gray"]),
    ]
    for x, y, txt, size, weight, color in entries:
        ax.text(x, y, txt, transform=ax.transAxes,
                ha="center", va="center",
                fontsize=size, fontweight=weight, color=color,
                multialignment="center")

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.5)
        spine.set_edgecolor("#CCCCCC")


# ---------------------------------------------------------------------------
# Figure 1: HRI computation  (flow strip + 4 maps)
# ---------------------------------------------------------------------------

def make_figure_hri(gdf, gdf_all):
    print("\n[1/2] HRI figure ...")
    fig = plt.figure(figsize=(16, 6.5), facecolor="white")
    gs = GridSpec(2, 4, figure=fig,
                  height_ratios=[0.55, 2],
                  hspace=0.38, wspace=0.18)

    ax_flow = fig.add_subplot(gs[0, :])
    ax_haz  = fig.add_subplot(gs[1, 0])
    ax_exp  = fig.add_subplot(gs[1, 1])
    ax_vul  = fig.add_subplot(gs[1, 2])
    ax_hri  = fig.add_subplot(gs[1, 3])

    draw_flow_strip(ax_flow)
    render_map(ax_haz, gdf, gdf_all, "hazard")
    render_map(ax_exp, gdf, gdf_all, "exposure")
    render_map(ax_vul, gdf, gdf_all, "vulnerability")
    render_map(ax_hri, gdf, gdf_all, "hri")

    # Operator symbols after layout is drawn
    fig.canvas.draw()
    for sym, la, ra in zip(["×", "×", "="],
                           [ax_haz, ax_exp, ax_vul],
                           [ax_exp, ax_vul, ax_hri]):
        xm = (la.get_position().x1 + ra.get_position().x0) / 2
        ym = (la.get_position().y0 + la.get_position().y1) / 2
        fig.text(xm, ym, sym, ha="center", va="center",
                 fontsize=18, fontweight="bold", color="#444444")

    out = MAPS_DIR / "map_process_hri.png"
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  → {out.name}  ({out.stat().st_size/1e6:.1f} MB)")


# ---------------------------------------------------------------------------
# Figure 2: Shelter computation  (3 maps + card)
# ---------------------------------------------------------------------------

def make_figure_shelter(gdf, gdf_all):
    print("\n[2/2] Shelter figure ...")
    fig = plt.figure(figsize=(16, 5.5), facecolor="white")
    gs = GridSpec(1, 4, figure=fig, wspace=0.18)

    ax_grn  = fig.add_subplot(gs[0, 0])
    ax_ohsi = fig.add_subplot(gs[0, 1])
    ax_ihsi = fig.add_subplot(gs[0, 2])
    ax_card = fig.add_subplot(gs[0, 3])

    render_map(ax_grn,  gdf, gdf_all, "green")
    render_map(ax_ohsi, gdf, gdf_all, "ohsi")
    render_map(ax_ihsi, gdf, gdf_all, "ihsi")
    draw_card(ax_card, gdf)

    fig.suptitle("Shelter Supply Indices — From Resources to Normalized Scores",
                 fontsize=12, fontweight="bold", y=1.01, color=C["dark"])

    out = MAPS_DIR / "map_process_shelter.png"
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  → {out.name}  ({out.stat().st_size/1e6:.1f} MB)")


# ---------------------------------------------------------------------------
# Individual map exports
# ---------------------------------------------------------------------------

INDIVIDUAL_MAPS = [
    ("hazard",        "map_process_hazard.png"),
    ("exposure",      "map_process_exposure.png"),
    ("vulnerability", "map_process_vulnerability.png"),
    ("hri",           "map_process_hri_solo.png"),
    ("green",         "map_process_green.png"),
    ("ohsi",          "map_process_ohsi.png"),
    ("ihsi",          "map_process_ihsi.png"),
    ("ohspi",         "map_process_ohspi.png"),
    ("ihspi",         "map_process_ihspi.png"),
]


def make_individual_maps(gdf, gdf_all):
    print("\n[Individual maps] ...")
    for key, fname in INDIVIDUAL_MAPS:
        fig, ax = plt.subplots(figsize=(6, 7), facecolor="white")
        render_map(ax, gdf, gdf_all, key, legend=True)
        fig.tight_layout(pad=0.5)
        out = MAPS_DIR / fname
        fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(f"  → {fname}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    gdf_all, gdf = load_data()
    MAPS_DIR.mkdir(parents=True, exist_ok=True)

    make_figure_hri(gdf, gdf_all)
    make_figure_shelter(gdf, gdf_all)
    make_individual_maps(gdf, gdf_all)

    print("\nAll done.")


if __name__ == "__main__":
    main()
