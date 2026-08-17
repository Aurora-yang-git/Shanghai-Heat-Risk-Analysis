#!/usr/bin/env python3
"""
08_visualize.py -- Generate thematic maps for Shanghai heat-risk analysis.

Produces 5 maps (urban core scope — 7 central districts):
  1. HRI Heat Risk Map (7-class Jenks, YlOrRd)
  2. OHSPI Outdoor Priority Map (4-category: Adequate/Low/Medium/High)
  3. IHSPI Indoor Priority Map (4-category: Adequate/Low/Medium/High)
  4. Priority Composite -- dual-panel OHSPI + IHSPI
  5. Supply-Demand Dashboard -- 5-subplot overview

Zero-population blocks outside the urban core are shown as a neutral gray
underlay (loaded from the full BLOCKS_FILE for geographic context).
District boundaries are overlaid as outlines.
"""

import sys
import warnings
from pathlib import Path

import contextily as ctx
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.colors import ListedColormap

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    BLOCKS_FILE, BLOCKS_URBAN_FILE, MAPS_DIR,
    URBAN_DISTRICTS_FILE, JENKS_CLASSES,
)

warnings.filterwarnings("ignore")

try:
    from matplotlib_scalebar.scalebar import ScaleBar
    HAS_SCALEBAR = True
except ImportError:
    HAS_SCALEBAR = False

TILE_SOURCES = [
    ctx.providers.CartoDB.Positron,
    "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    ctx.providers.Stadia.StamenTonerLite,
]

# 4-tier priority colormap: Adequate=gray, Low=yellow, Medium=orange, High=red
PRIORITY_CMAP = ListedColormap(["#AAAAAA", "#FFFF00", "#FF8C00", "#CC0000"])
PRIORITY_CATS = ["Adequate", "Low", "Medium", "High"]
PRIORITY_COLORS = ["#AAAAAA", "#FFFF00", "#FF8C00", "#CC0000"]

# Bivariate choropleth zones: PRIORITY/Watch/Safe/Adequate
BIVAR_ZONES = ["PRIORITY", "Watch", "Safe", "Adequate"]
BIVAR_COLORS = ["#d7191c", "#9467bd", "#cccccc", "#2c7bb6"]

# Neutral fill for in-boundary areas with no block data (rivers, rail yards,
# unclassified land). Distinct from Safe #cccccc / Adequate #AAAAAA grays.
NO_DATA_FILL = "#EDE8DC"

# District romanized names for map labels (Chinese → English)
DISTRICT_ROMANIZED = {
    "黄浦区": "Huangpu", "徐汇区": "Xuhui", "长宁区": "Changning",
    "静安区": "Jing'an", "普陀区": "Putuo", "虹口区": "Hongkou", "杨浦区": "Yangpu",
}


def add_basemap(ax, crs):
    for src in TILE_SOURCES:
        try:
            # Attribution moved to the figure footer — the on-map stamp
            # collides with the bivariate 2×2 legend.
            ctx.add_basemap(ax, crs=crs, source=src, zoom=12, alpha=0.6,
                            attribution=False)
            return
        except Exception:
            continue
    ax.set_facecolor("#f5f5f5")


def add_north_arrow(ax, x=0.95, y=0.95):
    ax.annotate("N", xy=(x, y), xycoords="axes fraction",
                fontsize=14, fontweight="bold", ha="center", va="center")
    ax.annotate("", xy=(x, y - 0.01), xytext=(x, y - 0.06),
                xycoords="axes fraction",
                arrowprops=dict(arrowstyle="->", lw=2, color="black"))


def add_scale_bar(ax):
    if HAS_SCALEBAR:
        sb = ScaleBar(1, "m", location="lower left", length_fraction=0.2)
        ax.add_artist(sb)


def add_district_overlay(ax, districts):
    """Draw district boundaries as outlines over the map."""
    if districts is not None:
        districts.boundary.plot(ax=ax, edgecolor="#444444", linewidth=1.2,
                                linestyle="--", alpha=0.8)


def add_study_area_fill(ax, districts):
    """Solid fill under the study area so data gaps don't show the basemap.

    Opaque on purpose: with alpha, overlapping district edges render as seams.
    Draw after the gray context underlay and before the thematic blocks.
    """
    if districts is not None:
        districts.plot(ax=ax, color=NO_DATA_FILL, edgecolor="none")


def add_district_labels(ax, districts):
    """Annotate each district with its romanized name at the centroid."""
    if districts is None or "name" not in districts.columns:
        return
    for _, row in districts.iterrows():
        pt = row.geometry.centroid
        label = DISTRICT_ROMANIZED.get(row["name"], row["name"])
        ax.annotate(
            label, xy=(pt.x, pt.y), xycoords="data",
            fontsize=7.5, ha="center", va="center",
            fontweight="bold", color="#1a1a1a",
            bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                      alpha=0.75, edgecolor="none"),
        )


def add_source_footer(fig, extra=""):
    """Add a small source attribution line at the bottom of the figure."""
    base = ("Data: OpenStreetMap 2022 · Population: WorldPop · Nightlight: VIIRS"
            " · Basemap: © OpenStreetMap contributors, © CARTO")
    text = f"{base} · {extra}" if extra else base
    fig.text(0.5, 0.002, text, ha="center", fontsize=6.5,
             color="#888888", style="italic")


def _add_bivariate_legend(fig, ax):
    """Draw a 2×2 bivariate legend grid inside the lower-left of the map axes."""
    # Use figure-fraction coordinates derived from the axes bbox
    pos = ax.get_position()
    # Legend occupies 12% of figure width and height, inside the axes lower-left
    lw = 0.11 * (pos.x1 - pos.x0)
    lh = 0.11 * (pos.y1 - pos.y0)
    lx = pos.x0 + 0.015 * (pos.x1 - pos.x0)
    ly = pos.y0 + 0.015 * (pos.y1 - pos.y0)

    axl = fig.add_axes([lx, ly, lw * 2, lh * 2])

    # 2x2 grid — columns = HRI (low left, high right), rows = shelter (low bottom, high top)
    cells = [
        (0, 0, "#cccccc", "Safe"),       # Low HRI + Low Shelter
        (1, 0, "#d7191c", "PRIORITY"),   # High HRI + Low Shelter
        (0, 1, "#2c7bb6", "Adequate"),   # Low HRI + High Shelter
        (1, 1, "#9467bd", "Watch"),      # High HRI + High Shelter
    ]
    for col, row, color, label in cells:
        rect = mpatches.FancyBboxPatch(
            (col, row), 1, 1,
            boxstyle="square,pad=0",
            facecolor=color, edgecolor="white", linewidth=1,
        )
        axl.add_patch(rect)
        txt_color = "white" if color != "#cccccc" else "#333333"
        axl.text(col + 0.5, row + 0.5, label,
                 ha="center", va="center", fontsize=5.5,
                 fontweight="bold", color=txt_color)

    axl.set_xlim(0, 2)
    axl.set_ylim(0, 2)
    axl.set_xticks([0, 2])
    axl.set_xticklabels(["Low", "High"], fontsize=5.5)
    axl.set_yticks([0, 2])
    axl.set_yticklabels(["Low", "High"], fontsize=5.5)
    axl.set_xlabel("Heat Risk →", fontsize=6, labelpad=1)
    axl.set_ylabel("↑ Shelter", fontsize=6, labelpad=1)
    axl.tick_params(length=0, pad=1)
    for spine in ["top", "right"]:
        axl.spines[spine].set_visible(False)


def zoom_to_urban(ax, gdf_active, buffer_pct=0.08):
    """Set axis extent to urban core bounds with a small buffer."""
    b = gdf_active.total_bounds  # (minx, miny, maxx, maxy)
    dx = (b[2] - b[0]) * buffer_pct
    dy = (b[3] - b[1]) * buffer_pct
    ax.set_xlim(b[0] - dx, b[2] + dx)
    ax.set_ylim(b[1] - dy, b[3] + dy)


def plot_classified_map(
    gdf_all: gpd.GeoDataFrame,
    gdf_active: gpd.GeoDataFrame,
    districts: gpd.GeoDataFrame,
    column: str,
    cmap: str,
    title: str,
    filename: str,
    legend_title: str = "",
    k: int = JENKS_CLASSES,
):
    """Plot a Jenks-classified thematic map zoomed to the urban core."""
    print(f"\n  Generating {filename} ...")

    fig, ax = plt.subplots(1, 1, figsize=(10, 11))

    # Gray underlay for context blocks visible within the zoomed extent
    gdf_all.plot(ax=ax, color="#E8E8E8", edgecolor="#D0D0D0", linewidth=0.1)
    add_study_area_fill(ax, districts)

    n_unique = len(gdf_active[column].dropna().unique())
    actual_k = min(k, n_unique) if n_unique >= 2 else 2

    gdf_active.plot(
        column=column,
        cmap=cmap,
        scheme="quantiles",
        k=actual_k,
        ax=ax,
        edgecolor="none",
        linewidth=0,
        alpha=0.9,
        legend=True,
        legend_kwds={
            "title": legend_title or column,
            "loc": "lower right",
            "fontsize": 8,
            "title_fontsize": 10,
        },
    )

    add_district_overlay(ax, districts)
    add_district_labels(ax, districts)
    zoom_to_urban(ax, gdf_active)
    add_basemap(ax, gdf_all.crs)
    add_north_arrow(ax)
    add_scale_bar(ax)

    ax.set_title(title, fontsize=14, fontweight="bold", pad=10)
    ax.set_axis_off()
    add_source_footer(fig)
    plt.tight_layout(rect=[0, 0.02, 1, 1])

    png_path = MAPS_DIR / f"{filename}.png"
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"    [OK] {png_path.name} ({png_path.stat().st_size / 1e6:.1f} MB)")


def plot_priority_categorical(
    gdf_all: gpd.GeoDataFrame,
    gdf_active: gpd.GeoDataFrame,
    districts: gpd.GeoDataFrame,
    cat_column: str,
    val_column: str,
    title: str,
    filename: str,
):
    """Plot a 4-category priority map (Adequate / Low / Medium / High)."""
    print(f"\n  Generating {filename} ...")

    fig, ax = plt.subplots(1, 1, figsize=(10, 11))
    gdf_all.plot(ax=ax, color="#E8E8E8", edgecolor="#D0D0D0", linewidth=0.1)
    add_study_area_fill(ax, districts)

    cat_col = gdf_active[cat_column].astype(str)

    for cat, color in zip(PRIORITY_CATS, PRIORITY_COLORS):
        subset = gdf_active[cat_col == cat]
        if len(subset) > 0:
            subset.plot(ax=ax, color=color, edgecolor="none", linewidth=0, alpha=0.9)

    patches = [
        mpatches.Patch(color=color, label=f"{cat} ({(cat_col == cat).sum()})")
        for cat, color in zip(PRIORITY_CATS, PRIORITY_COLORS)
    ]
    ax.legend(handles=patches, loc="lower right", fontsize=8,
              title="Priority Category", title_fontsize=10)

    n_high = (cat_col == "High").sum()
    add_district_overlay(ax, districts)
    add_district_labels(ax, districts)
    zoom_to_urban(ax, gdf_active)
    add_basemap(ax, gdf_all.crs)
    add_north_arrow(ax)
    add_scale_bar(ax)

    ax.set_title(
        f"{title}\n{n_high} blocks identified as HIGH priority for intervention",
        fontsize=13, fontweight="bold", pad=10,
    )
    ax.set_axis_off()
    add_source_footer(fig)
    plt.tight_layout(rect=[0, 0.02, 1, 1])

    png_path = MAPS_DIR / f"{filename}.png"
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"    [OK] {png_path.name} ({png_path.stat().st_size / 1e6:.1f} MB)")


def plot_priority_composite(gdf_all, gdf_active, districts):
    """Dual-panel OHSPI + IHSPI categorical maps with Top-10 annotations."""
    print("\n  Generating priority composite map ...")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 11))

    for ax, cat_col, val_col, title_suffix in [
        (ax1, "ohspi_cat", "ohspi", "Outdoor Green Space (OHSPI)"),
        (ax2, "ihspi_cat", "ihspi", "Indoor Facilities (IHSPI)"),
    ]:
        gdf_all.plot(ax=ax, color="#E8E8E8", edgecolor="#D0D0D0", linewidth=0.1)
        add_study_area_fill(ax, districts)

        cat_series = gdf_active[cat_col].astype(str)
        for cat, color in zip(PRIORITY_CATS, PRIORITY_COLORS):
            subset = gdf_active[cat_series == cat]
            if len(subset) > 0:
                subset.plot(ax=ax, color=color, edgecolor="none", linewidth=0, alpha=0.9)

        patches = [
            mpatches.Patch(color=color, label=f"{cat} ({(cat_series == cat).sum()})")
            for cat, color in zip(PRIORITY_CATS, PRIORITY_COLORS)
        ]
        ax.legend(handles=patches, loc="lower right", fontsize=8,
                  title="Priority", title_fontsize=9)

        add_district_overlay(ax, districts)
        add_district_labels(ax, districts)
        zoom_to_urban(ax, gdf_active)
        add_basemap(ax, gdf_all.crs)
        ax.set_title(
            f"Shelter Priority — {title_suffix}\nUrban Core: 7 Central Districts",
            fontsize=12, fontweight="bold",
        )
        ax.set_axis_off()

        top10 = gdf_active.nlargest(10, val_col)
        for _, row in top10.iterrows():
            c = row.geometry.centroid
            ax.annotate(
                f"#{row['block_id']}", xy=(c.x, c.y),
                fontsize=6, fontweight="bold", color="darkred", ha="center",
                bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.7, ec="red"),
            )

    plt.suptitle("Intervention Priority — Shanghai Urban Core 2022",
                 fontsize=16, fontweight="bold", y=1.01)
    plt.tight_layout()

    p = MAPS_DIR / "map_priority_composite.png"
    fig.savefig(p, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"    [OK] map_priority_composite.png ({p.stat().st_size / 1e6:.1f} MB)")


def plot_dashboard(gdf_all, gdf_active, districts):
    """5-subplot supply-demand dashboard."""
    print("\n  Generating dashboard ...")

    fig, axes = plt.subplots(2, 3, figsize=(24, 16))

    panels = [
        ("hri_norm", "YlOrRd", "Heat Risk Index (HRI)"),
        ("ohsi", "Greens", "Outdoor Shelter Supply (OHSI)"),
        ("ihsi", "Blues", "Indoor Shelter Supply (IHSI)"),
    ]

    for ax, (col, cmap, title) in zip(axes.flat[:3], panels):
        gdf_all.plot(ax=ax, color="#E8E8E8", edgecolor="none", linewidth=0)
        add_study_area_fill(ax, districts)
        gdf_active.plot(
            column=col, cmap=cmap, scheme="quantiles",
            k=JENKS_CLASSES, ax=ax, edgecolor="none", linewidth=0,
            alpha=0.9, legend=True,
            legend_kwds={"fontsize": 6, "loc": "lower right"},
        )
        add_district_overlay(ax, districts)
        zoom_to_urban(ax, gdf_active)
        add_basemap(ax, gdf_all.crs)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_axis_off()

    # Priority panels (categorical)
    for ax, (cat_col, val_col, title) in zip(axes.flat[3:5], [
        ("ohspi_cat", "ohspi", "Outdoor Priority (OHSPI)"),
        ("ihspi_cat", "ihspi", "Indoor Priority (IHSPI)"),
    ]):
        gdf_all.plot(ax=ax, color="#E8E8E8", edgecolor="none", linewidth=0)
        add_study_area_fill(ax, districts)
        cat_series = gdf_active[cat_col].astype(str)
        for cat, color in zip(PRIORITY_CATS, PRIORITY_COLORS):
            subset = gdf_active[cat_series == cat]
            if len(subset) > 0:
                subset.plot(ax=ax, color=color, edgecolor="none", linewidth=0, alpha=0.9)
        patches = [mpatches.Patch(color=c, label=cat) for cat, c in zip(PRIORITY_CATS, PRIORITY_COLORS)]
        ax.legend(handles=patches, fontsize=6, loc="lower right")
        add_district_overlay(ax, districts)
        zoom_to_urban(ax, gdf_active)
        add_basemap(ax, gdf_all.crs)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_axis_off()

    axes[1, 2].set_visible(False)

    plt.suptitle(
        "Shanghai Urban Core Heat Risk — Supply-Demand Dashboard 2022\n"
        "7 Central Districts: Huangpu, Xuhui, Changning, Jing'an, Putuo, Hongkou, Yangpu",
        fontsize=14, fontweight="bold", y=1.01,
    )
    plt.tight_layout()

    p = MAPS_DIR / "map_dashboard.png"
    fig.savefig(p, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"    [OK] map_dashboard.png ({p.stat().st_size / 1e6:.1f} MB)")


def plot_bivariate_choropleth(gdf_all, gdf_active, districts):
    """Bivariate choropleth: HRI × mean(OHSI, IHSI) with 4 policy zones."""
    print("\n  Generating bivariate choropleth map ...")

    shelter = (gdf_active["ohsi"] + gdf_active["ihsi"]) / 2
    hri = gdf_active["hri_norm"]
    # Shelter is bimodal (61% at OSM floor ≈ 0.10, 39% above). Mean-based split
    # correctly detects the natural gap; median would collapse to the floor value.
    hri_split = hri.mean()
    shelter_split = shelter.mean()

    zone = np.where(
        (hri >= hri_split) & (shelter < shelter_split), "PRIORITY",
        np.where(
            (hri >= hri_split) & (shelter >= shelter_split), "Watch",
            np.where(
                (hri < hri_split) & (shelter >= shelter_split), "Adequate",
                "Safe",
            ),
        ),
    )
    gdf_plot = gdf_active.copy()
    gdf_plot["bivar_zone"] = zone

    color_map = dict(zip(BIVAR_ZONES, BIVAR_COLORS))

    fig, ax = plt.subplots(1, 1, figsize=(10, 11))
    gdf_all.plot(ax=ax, color="#E8E8E8", edgecolor="#D0D0D0", linewidth=0.1)
    add_study_area_fill(ax, districts)

    for z in BIVAR_ZONES:
        subset = gdf_plot[gdf_plot["bivar_zone"] == z]
        if len(subset) > 0:
            subset.plot(ax=ax, color=color_map[z], edgecolor="none",
                        linewidth=0, alpha=0.9)

    # Zone legend with block counts
    patches = [
        mpatches.Patch(color=color_map[z],
                       label=f"{z}  ({(gdf_plot['bivar_zone'] == z).sum()})")
        for z in BIVAR_ZONES
    ]
    patches.append(mpatches.Patch(color=NO_DATA_FILL, label="No data"))
    ax.legend(handles=patches, loc="lower right", fontsize=9,
              title="Policy Zone  (block count)", title_fontsize=10,
              framealpha=0.9)

    add_district_overlay(ax, districts)
    add_district_labels(ax, districts)
    zoom_to_urban(ax, gdf_active)
    add_basemap(ax, gdf_all.crs)
    add_north_arrow(ax)
    add_scale_bar(ax)

    n_priority = (gdf_plot["bivar_zone"] == "PRIORITY").sum()
    ax.set_title(
        f"Heat Risk × Shelter Supply — Bivariate Analysis\n"
        f"Urban Core (7 Districts) · {n_priority} blocks need urgent shelter intervention",
        fontsize=13, fontweight="bold", pad=10,
    )
    ax.set_axis_off()
    add_source_footer(fig, extra="Bivariate: mean-split on HRI and mean(OHSI, IHSI)")
    plt.tight_layout(rect=[0, 0.02, 1, 1])

    # Draw 2D bivariate legend grid (must come after tight_layout to get stable positions)
    _add_bivariate_legend(fig, ax)

    p = MAPS_DIR / "map_bivariate.png"
    fig.savefig(p, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"    [OK] map_bivariate.png ({p.stat().st_size / 1e6:.1f} MB)")


def main():
    print("=" * 60)
    print("STEP 8: Visualization")
    print("=" * 60)

    MAPS_DIR.mkdir(parents=True, exist_ok=True)

    # Full municipality blocks for gray underlay
    gdf_all = gpd.read_file(BLOCKS_FILE)
    print(f"\n  Full dataset (gray underlay): {len(gdf_all)} blocks")

    # Urban inhabited blocks (analysis scope)
    blocks = gpd.read_file(BLOCKS_URBAN_FILE)
    print(f"  Urban inhabited blocks: {len(blocks)}")

    # District boundaries for outline overlay
    districts = None
    if URBAN_DISTRICTS_FILE.exists():
        districts = gpd.read_file(URBAN_DISTRICTS_FILE).to_crs(blocks.crs)
        print(f"  District boundaries: {len(districts)} districts")
    else:
        print("  [WARN] District boundaries not found — skipping overlay")

    # Map 1: HRI (Jenks classified)
    plot_classified_map(
        gdf_all, blocks, districts, "hri_norm", "YlOrRd",
        "Heat Risk Index (HRI) — Urban Core, 7 Central Districts\nShanghai 2022",
        "map_hri", legend_title="HRI (7-class quantile)",
    )

    # Map 2: OHSPI (4-category)
    plot_priority_categorical(
        gdf_all, blocks, districts, "ohspi_cat", "ohspi",
        "Outdoor Heat Shelter Priority (OHSPI)\nUrban Core — 7 Central Districts",
        "map_ohspi",
    )

    # Map 3: IHSPI (4-category)
    plot_priority_categorical(
        gdf_all, blocks, districts, "ihspi_cat", "ihspi",
        "Indoor Heat Shelter Priority (IHSPI)\nUrban Core — 7 Central Districts",
        "map_ihspi",
    )

    # Map 4: Priority composite
    plot_priority_composite(gdf_all, blocks, districts)

    # Map 5: Dashboard
    plot_dashboard(gdf_all, blocks, districts)

    # Map 6: Bivariate choropleth (HRI × combined shelter)
    plot_bivariate_choropleth(gdf_all, blocks, districts)

    print("\n" + "=" * 60)
    print(f"Visualization complete — {len(list(MAPS_DIR.glob('*.png')))} PNG files")
    print("=" * 60)


if __name__ == "__main__":
    main()
