---
tags:
  - grade/G11
  - type/project
  - status/active
last_archived: 2026-06-05
---

# Heat Risk Index and Shelter Priority Model — Technical Specification

> Shanghai Block-Level Extreme Heat Risk Assessment and Shelter Supply-Demand Matching
>
> Reference implementation: Yang, A. (2025). *Mapping priority zones for urban heat mitigation in Shanghai: Heat risk vs. shelter provision.* Computers, Environment and Urban Systems, 117, 102283. [doi:10.1016/j.compenvurbsys.2025.102283](https://www.sciencedirect.com/science/article/abs/pii/S0198971525000833)

---

## 1. Problem Statement

Extreme heat events in Shanghai (24.9 M residents, subtropical monsoon climate) are intensifying under climate change and rapid urbanisation. Conventional heat-risk maps based on Land Surface Temperature (LST) fail on two counts:

1. **LST ≠ human thermal stress.** Rooftop radiative temperature diverges from pedestrian-level physiological heat load.
2. **Risk maps without resource context are not actionable.** Knowing *where it is hot* is insufficient — planners need to know *where it is hot AND cooling resources are missing*.

This model addresses both gaps by computing a multiplicative Heat Risk Index ($\text{HRI}$) from human-biometeorology data, then subtracting spatially explicit shelter supply indices to identify **intervention priority zones**.

---

## 2. Notation

| Symbol | Definition | Unit |
|--------|-----------|------|
| $H_i$ | Heat Hazard index for block $i$ | dimensionless [0.1, 0.9] |
| $E_i$ | Heat Exposure index for block $i$ | dimensionless [0.1, 0.9] |
| $V_i$ | Heat Vulnerability index for block $i$ | dimensionless [0.1, 0.9] |
| $\text{HRI}_i$ | Heat Risk Index for block $i$ | dimensionless |
| $T_i$ | UTCI mean value for block $i$ | °C |
| $PD_i$ | Population density for block $i$ | persons/km² |
| $POP_i$ | Total population within block $i$ | persons |
| $NL_i$ | Nighttime light intensity for block $i$ | DN |
| $GDP_i$ | Gridded GDP for block $i$ | USD PPP |
| $GSA_i$ | Green space area within block $i$ | m² |
| $POID_i$ | Weighted POI density for block $i$ | weighted count/km² |
| $W_T^{(k)}$ | Operating-time weight for shelter type $k$ | dimensionless [0, 1] |
| $\text{OHSI}_i$ | Outdoor Heat Shelter Index for block $i$ | dimensionless [0.1, 0.9] |
| $\text{IHSI}_i$ | Indoor Heat Shelter Index for block $i$ | dimensionless [0.1, 0.9] |
| $\text{OHSPI}_i$ | Outdoor Heat Shelter Priority Index for block $i$ | dimensionless |
| $\text{IHSPI}_i$ | Indoor Heat Shelter Priority Index for block $i$ | dimensionless |
| $\mathcal{N}^{+}(\cdot)$ | Positive normalisation (higher → higher) | — |
| $\mathcal{N}^{-}(\cdot)$ | Negative normalisation (higher → lower) | — |

---

## 3. Assumptions and Justifications

**A1.** Heat risk is a **multiplicative** interaction: $\text{HRI} = H \times E \times V$. A block with zero population has near-zero $\text{HRI}$ regardless of thermal intensity.
- An additive model ($H + E + V$) would assign moderate risk to uninhabited blocks with extreme UTCI — epidemiologically meaningless, since heat mortality requires people. The multiplicative form ensures risk is only high when all three dimensions co-occur (IPCC AR6; Yang, 2025).

**A2.** UTCI adequately represents pedestrian-level thermal stress. Monthly-mean GloUTCI-M (August 2022) serves as the static Hazard ($H$) proxy.
- UTCI integrates air temperature, humidity, wind speed, and mean radiant temperature via a multi-node thermoregulation model. LST only measures rooftop radiative temperature, diverging from street-level thermal load by up to 10–15°C in urban canyons. August is Shanghai's peak heat month (climatological $T_{\max}$ > 35°C).

**A3.** OSM building footprint area is proportional to residential population. Total footprint is scaled to 24.9 M to derive Population Density ($PD_i$) for Exposure ($E$).
- Building footprint correlates with floor area and occupancy — a standard proxy when census-calibrated gridded data (e.g., WorldPop 5.4 GB) is inaccessible. Limitation: industrial/commercial buildings inflate estimates in non-residential zones.

**A4.** Nighttime light ($NL_i$) and gridded GDP ($GDP_i$) are **negative** proxies for Vulnerability ($V$) — higher values indicate greater adaptive capacity.
- Brighter nightlight → denser infrastructure, higher AC penetration, better-maintained housing (Chen et al., 2021). Higher GDP → purchasing power for cooling, healthcare access, housing insulation (Kummu et al., 2024). Both are established socio-economic resilience proxies in heat vulnerability literature. Population density is **excluded** from $V$ because it already appears in Exposure ($E$) — including it in both would double-weight it in the HRI product and conflate thermal exposure with demographic vulnerability.

**A5.5.** OHSI and IHSI are computed by **percentile rank normalization** within the urban core blocks, rather than min-max normalization across all 73,270 blocks.
- Min-max across all blocks assigns 0.1 (minimum) to 89–91% of blocks (those with zero green space or no POIs), making the maps visually uniform. Percentile ranking reveals relative shelter access among urban blocks: the best-served urban block receives 0.9, the worst-served receives 0.1, and blocks with zero shelter all tie at 0.1. This is a relative index, not an absolute adequacy threshold.

**A6.** Cooling shelters split into outdoor ($\text{OHSI}$, green space) and indoor ($\text{IHSI}$, commercial/cultural/transit POIs), each weighted by operating-time $W_T$.
- In Shanghai, indoor air-conditioned spaces (malls, metro, cafés) are the primary extreme-heat refuge — distinct from cities where parks dominate. Separating the two enables targeted policy: green space investment vs. extended building opening hours. $W_T$ reflects that a metro station (17 h/day) provides more shelter-hours than a library (8 h/day).

**A7.** Road-enclosed blocks reflect urban morphology better than regular grids. A 500 m fishnet fills gaps where road networks are sparse.
- Road blocks vary with density: 100–200 m in the city centre (matching the "15-minute life circle"), 500–1400 m in suburbs. A uniform grid would over-segment dense areas and under-segment sparse ones. The fishnet backfill ensures 100% coverage without sacrificing morphological fidelity.

---

## 4. Data Preparation

### 4.1 Data Sources

| Dataset | Source | Native resolution | Download |
|---------|--------|-------------------|----------|
| GloUTCI-M (Aug 2022) | Yao et al. (2023), CatBoost-downscaled global monthly UTCI | ~930 m | [zenodo.org/records/8310513](https://zenodo.org/records/8310513) |
| Population proxy | OSM Geofabrik Shanghai (2026-03-29), 148,117 building footprints rasterised, scaled to 24.9 M | ~100 m | [geofabrik.de](https://download.geofabrik.de/asia/china/shanghai-latest-free.shp.zip) |
| PCNL Nightlight 2021 | Chen et al. (2021), DMSP-OLS / NPP-VIIRS harmonised | ~860 m (500 m nominal) | [zenodo.org/records/7612389](https://zenodo.org/records/7612389) |
| Gridded GDP (2020) | Kummu et al. (2024), sub-national downscaled GDP PPP, 30 arc-second | ~860 m | [zenodo.org/records/13943886](https://zenodo.org/records/13943886) |
| OSM roads, landuse, POIs, transport | OpenStreetMap via Geofabrik Shanghai extract (2026-03-29) | Vector (street-level) | [geofabrik.de](https://download.geofabrik.de/asia/china/shanghai-latest-free.shp.zip) |

### 4.2 Preprocessing

All rasters are clipped to the Shanghai bounding box (120.85°E–122.00°E, 30.68°N–31.88°N) and reprojected to EPSG:32651 (UTM Zone 51N) for metric-unit area calculations. UTCI raw values (Int16) are divided by 100 to obtain °C. GDP uses the last band (year 2020) of the multi-temporal stack. NoData pixels are set to NaN and excluded from zonal statistics.

### 4.3 Spatial Unit Construction

```mermaid
flowchart LR
    A["OSM Roads\n205,444 segments"] --> B["Filter 6 classes\nmotorway, trunk, primary,\nsecondary, tertiary, residential"]
    B --> C["unary_union()\n+ Shanghai boundary ring"]
    C --> D["shapely.polygonize()"]
    D --> E["24,214 road-enclosed blocks\n(56% area coverage)"]
    F["Shanghai boundary\n(from OSM road extents)"] --> G["Subtract road-block union"]
    G --> H["Generate 500 m × 500 m\nfishnet on uncovered area"]
    H --> I["49,056 fishnet cells"]
    E --> J["Merge → 73,270 blocks\n100% area coverage"]
    I --> J
```

Road-enclosed blocks capture urban morphology: dense city-centre blocks have 100–200 m equivalent side lengths; suburban blocks reach 500–1400 m. The fishnet infill covers the remaining 44% (rural areas, water margins, Chongming Island) where road networks do not form closed polygons.

### 4.4 Resolution Matching

| Dataset | Pixel size (UTM) | Shanghai coverage | Adequacy for block-level analysis |
|---------|-----------------|-------------------|-----------------------------------|
| GloUTCI-M (UTCI) | ~930 m | 27,150 px | ⚠️ Multiple urban blocks share one pixel — spatial smoothing in city centre |
| Population proxy | ~100 m | 1,396,425 px | ✅ Finer than most blocks; multiple pixels per block |
| PCNL Nightlight | ~860 m | 31,785 px | ⚠️ Comparable to block scale; adequate for mean statistics |
| Gridded GDP | ~860 m | 31,785 px | ✅ Upgraded from 5-arcmin (8.6 km, only 304 px) to 30-arcsec; now matches NL and UTCI |

### 4.5 Zonal Statistics

Each of the 73,270 blocks receives aggregated values from the four rasters and two vector layers:

| Zonal operation | Source | Output variable | Statistic |
|----------------|--------|-----------------|-----------|
| Raster mean | UTCI | $T_i$ (UTCI, °C) | mean of all pixels whose centre falls within block $i$ |
| Raster sum | Population | $POP_i$ (persons) | sum of population pixels; $PD_i = POP_i / \text{area}_{km^2}$ |
| Raster mean | Nightlight | $NL_i$ (DN) | mean nightlight intensity |
| Raster mean | GDP | $GDP_i$ (USD PPP) | mean gridded GDP |
| Vector intersection | OSM landuse (green classes) | $GSA_i$ (m²) | total green polygon area clipped to block $i$ |
| Vector spatial join | OSM POIs + transport (shelter classes) | $POID_i$ (weighted count/km²) | $\sum W_T^{(k)} \cdot n_k$ for each shelter type $k$ within block $i$, divided by block area |

---

## 4a. Study Area

### Urban Core Scope

This analysis focuses on Shanghai's **7 central urban districts** rather than the full 6,340 km² municipality:

| District (CN) | District (EN) | Area (km²) | Urban blocks |
|--------------|---------------|------------|--------------|
| 黄浦区 | Huangpu | 20.6 | 589 |
| 徐汇区 | Xuhui | 55.2 | 606 |
| 长宁区 | Changning | 37.2 | 479 |
| 静安区 | Jing'an | 36.7 | 554 |
| 普陀区 | Putuo | 55.8 | 524 |
| 虹口区 | Hongkou | 23.4 | 420 |
| 杨浦区 | Yangpu | 60.5 | 682 |
| **Total** | | **289.4 km²** | **3,854 blocks** |

All 3,854 urban core blocks have $\text{pop\_sum} > 0$ (the urban core has no uninhabited road-enclosed blocks). District boundaries are sourced from OpenStreetMap via Nominatim and clipped to the Shanghai bounding box.

**Rationale for urban core scope:**
1. **Policy relevance**: Shanghai's extreme heat intervention programs target the densely inhabited urban core. Rural fringe and industrial zones (61.8% of the 73,270 total blocks are uninhabited) generate no heat mortality and dilute spatial differentiation in the maps.
2. **OSM data quality**: OSM POI coverage in the urban core (~2,000 POIs per 100 km²) is substantially better than suburban areas, making the IHSI more reliable within this area.
3. **Morphological homogeneity**: The 7 central districts share similar urban form (high-density residential interspersed with commercial corridors), making block-to-block comparison of OHSI and IHSI methodologically sound.

### Data Limitations

**OSM POI undercounting**: OSM records approximately 7,982 indoor shelter POIs across all of Shanghai (3,920 restaurants, 1,516 cafes, 895 fast_food, etc.). Real-world counts from Gaode or Baidu are approximately 20× higher. IHSI therefore captures **relative access to de-facto mapped shelters**, not all actual indoor cooling options. Two blocks with IHSI = 0.1 (minimum) are both shelter-poor relative to the urban core — one may have one unmapped café, the other none.

**Green space (OHSI) undercounting**: OSM landuse polygons do not include private/internal green areas within residential compounds (小区绿化), which can account for 30–50% of actual green area in Shanghai residential blocks. OHSI therefore underestimates green space availability in high-density residential districts.

**Population proxy**: OSM building footprint area ≠ census-calibrated population. Industrial and commercial buildings inflate estimated $PD_i$ in non-residential zones.

---

## 5. Model Architecture

```mermaid
flowchart TD
    subgraph DATA["📦 Data (Section 4)"]
        UTCI["GloUTCI-M\n~930 m"]
        POP["Population Proxy\n~100 m"]
        NL["PCNL Nightlight\n~860 m"]
        GDP["Gridded GDP\n~860 m"]
        LU["OSM landuse\n(green space)"]
        POI["OSM POIs + transport\n(indoor shelters)"]
    end

    subgraph ZONAL["📊 Zonal Stats → per block i"]
        UTCI --> Z_T["T_i"]
        POP --> Z_PD["POP_i, PD_i"]
        NL --> Z_NL["NL_i"]
        GDP --> Z_GDP["GDP_i"]
        LU --> Z_GSA["GSA_i"]
        POI --> Z_POI["POID_i, W̄_T"]
    end

    subgraph HRI["🔥 Heat Risk Index — HRI (Section 6)"]
        Z_T --> HAZ["Hazard H_i = 𝒩⁺(T_i)"]
        Z_PD --> EXP["Exposure E_i = 𝒩⁺(PD_i)"]
        Z_NL --> VUL["Vulnerability V_i =\n½[𝒩⁻(NL_i) + 𝒩⁻(GDP_i)]"]
        Z_GDP --> VUL
        HAZ --> MULT["HRI_i = H_i × E_i × V_i"]
        EXP --> MULT
        VUL --> MULT
        MULT --> NORM_HRI["HRI_norm = 𝒩⁺(HRI_i)"]
    end

    subgraph SHELTER["🏠 Shelter Supply (Section 7)"]
        Z_GSA --> OHSI["Outdoor Heat Shelter Index\nOHSI_i = rank_normalize(GSA_i / POP_i)"]
        Z_PD --> OHSI
        Z_POI --> IHSI["Indoor Heat Shelter Index\nIHSI_i = rank_normalize(POID_i / PD_i × W̄_T)"]
        Z_PD --> IHSI
    end

    subgraph PRIORITY["⚡ Priority (Section 8)"]
        NORM_HRI --> OHSPI["OHSPI_i = HRI_norm − OHSI_i"]
        OHSI --> OHSPI
        NORM_HRI --> IHSPI["IHSPI_i = HRI_norm − IHSI_i"]
        IHSI --> IHSPI
    end
```

### Data → Indicator Mapping

| Raw dataset | Zonal stat | Feeds into | Formula | $\mathcal{N}$ direction |
|-------------|-----------|------------|---------|------------------------|
| GloUTCI-M (°C) | mean → $T_i$ | Hazard $H_i$ | $\mathcal{N}^{+}(T_i)$ | + : hotter → riskier |
| Population (buildings) | sum → $POP_i$, density → $PD_i$ | Exposure $E_i$ | $\mathcal{N}^{+}(PD_i)$ | + : denser → more exposed |
| PCNL Nightlight (DN) | mean → $NL_i$ | Vulnerability $V_i$ (½) | $\mathcal{N}^{-}(NL_i)$ | − : brighter → less vulnerable |
| Gridded GDP (USD PPP) | mean → $GDP_i$ | Vulnerability $V_i$ (½) | $\mathcal{N}^{-}(GDP_i)$ | − : richer → less vulnerable |
| OSM landuse (green) | area → $GSA_i$ | Outdoor Heat Shelter Index $\text{OHSI}_i$ | $\text{rank\_normalize}(GSA_i / POP_i)$ | relative: more green/capita → higher rank |
| OSM POIs + transport | weighted count → $POID_i$ | Indoor Heat Shelter Index $\text{IHSI}_i$ | $\text{rank\_normalize}(POID_i / PD_i \times \bar{W}_T)$ | relative: more POI/capita → higher rank |

---

## 6. Normalisation

All indicators are mapped to $[0.1, 0.9]$ to prevent multiplication-by-zero:

$$
\mathcal{N}^{+}(I) = 0.1 + 0.8 \cdot \frac{I - I_{\min}}{I_{\max} - I_{\min}}
$$

$$
\mathcal{N}^{-}(I) = 0.1 + 0.8 \cdot \frac{I_{\max} - I}{I_{\max} - I_{\min}}
$$

where $I_{\min}$ and $I_{\max}$ are computed within the **3,854 urban core blocks** (inhabited blocks in the 7 central districts). OHSI and IHSI use percentile rank normalization instead; see Section 8.

---

## 7. Heat Risk Index ($\text{HRI}$)

### 7.1 Hazard ($H_i$)

$$
H_i = \mathcal{N}^{+}(T_i)
$$

$T_i$ is the mean UTCI (°C) for block $i$, derived from GloUTCI-M August 2022 (Yao et al., 2023). UTCI integrates air temperature, humidity, wind speed, and mean radiant temperature through a multi-node human thermoregulation model.

### 7.2 Exposure ($E_i$)

$$
E_i = \mathcal{N}^{+}(PD_i)
$$

Population density ($PD_i$, persons/km²) serves as both a direct exposure measure and an indirect proxy for anthropogenic heat emission intensity.

### 7.3 Vulnerability ($V_i$)

$$
V_i = \frac{1}{2}\Big[\mathcal{N}^{-}(NL_i) + \mathcal{N}^{-}(GDP_i)\Big]
$$

| Sub-indicator | $\mathcal{N}$ | Rationale |
|--------------|---------------|-----------|
| Nightlight $NL_i$ | $\mathcal{N}^{-}$ | Higher luminosity → better infrastructure, AC penetration |
| GDP $GDP_i$ | $\mathcal{N}^{-}$ | Higher GDP → greater adaptive capacity |

Population density ($PD_i$) is **excluded** from $V_i$ to avoid double-counting: $PD_i$ already determines Exposure ($E_i$), and including it in $V_i$ would inflate its weight in the product $H \times E \times V$. The full model (Yang, 2025) uses 5 sub-indicators: $NL$, $GDP$, house prices, elderly density ($PD_{>65}$), child density ($PD_{<14}$). We use 2 due to data constraints (age-sex data: 51 GB; house prices: manual scraping required).

### 7.4 Multiplicative Aggregation

$$
\text{HRI}_i = H_i \times E_i \times V_i
$$

**Why multiplicative, not additive?** An additive model ($H + E + V$) would assign moderate risk to uninhabited blocks with extreme UTCI. The multiplicative form ensures risk is only high when **all three dimensions co-occur**, consistent with epidemiological evidence on heat mortality.

Re-normalised for mapping:

$$
\text{HRI}_i^{\text{norm}} = \mathcal{N}^{+}(\text{HRI}_i)
$$

---

## 8. Shelter Supply Indices

### 8.1 Outdoor Heat Shelter Index ($\text{OHSI}$)

Green spaces provide cooling through canopy shading and evapotranspiration.

$$
\text{OHSI}_i = \text{rank\_normalize}\!\left(\frac{GSA_i}{\max(POP_i,\; 1)}\right)
$$

where $\text{rank\_normalize}(x)$ maps the percentile rank of $x$ within the urban core blocks to $[0.1, 0.9]$. Blocks with zero green space all receive 0.1 (tied at minimum). Green space classes from OSM `landuse_a`: `park`, `forest`, `grass`, `recreation_ground`, `meadow`, `nature_reserve`.

82.5% of urban core blocks have zero green space per capita. This is a real finding (green space is scarce in central Shanghai) combined with OSM undercounting of private green areas inside residential compounds.

### 8.2 Indoor Heat Shelter Index ($\text{IHSI}$)

Air-conditioned public spaces serve as last-resort refuges during extreme heat.

$$
\text{IHSI}_i = \text{rank\_normalize}\!\left(\frac{POID_i}{\max(PD_i,\; 0.001)} \cdot \bar{W}_T^{(i)}\right)
$$

72.4% of urban core blocks have no mapped indoor shelter POIs. OSM POI density in China is approximately 20× lower than proprietary sources (Gaode, Baidu), so IHSI captures relative access among de-facto mapped shelters, not all actual indoor cooling options.

| Shelter category | OSM fclass | $W_T$ | Hours |
|-----------------|-----------|-------|-------|
| Mall / Commercial | `mall`, `department_store`, `supermarket` | 0.50 | 10:00–22:00 |
| Restaurant / Café | `restaurant`, `cafe`, `fast_food`, `food_court`, `bar`, `bakery` | 0.625 | 07:00–22:00 |
| Cultural / Public | `museum`, `library`, `cinema`, `theatre`, `arts_centre`, `community_centre` | 0.33 | 09:00–17:00 |
| Metro / Transit | `railway_station` | 0.71 | 06:00–23:00 |

---

## 9. Intervention Priority Indices

$$
\text{OHSPI}_i = \text{HRI}_i^{\text{norm}} - \text{OHSI}_i
$$

$$
\text{IHSPI}_i = \text{HRI}_i^{\text{norm}} - \text{IHSI}_i
$$

- $> 0$: block has **more risk than shelter supply** → priority intervention zone
- $= 0$: shelter supply exactly matches heat risk → adequate
- $< 0$: block has **surplus** cooling capacity relative to its risk level

OHSPI and IHSPI range approximately $[-0.8,\; +0.8]$ because $\text{HRI}^{\text{norm}} \in [0.1, 0.9]$ and $\text{OHSI}/\text{IHSI} \in [0.1, 0.9]$. Negative values are **not anomalies** — they mean shelter supply exceeds local heat risk.

### 9.1 Priority Categories

Maps use 4 ordered categories to make findings interpretable to non-GIS judges and policy audiences:

| Category | OHSPI / IHSPI range | Interpretation | Urban core (OHSPI) | Urban core (IHSPI) |
|----------|---------------------|----------------|--------------------|-------------------|
| **Adequate** | $< 0$ | Shelter supply exceeds risk | 675 blocks (17.5%) | 1,061 blocks (27.5%) |
| **Low** | $[0,\; 0.1)$ | Small gap; monitor | 443 blocks (11.5%) | 402 blocks (10.4%) |
| **Medium** | $[0.1,\; 0.3)$ | Moderate gap; plan investment | 2,414 blocks (62.6%) | 2,077 blocks (53.9%) |
| **High** | $\geq 0.3$ | Large gap; immediate intervention | 322 blocks (8.4%) | 314 blocks (8.1%) |

**Key finding**: 62.6% of urban core blocks show medium outdoor shelter priority; 8.4% show high priority. Indoor gaps are slightly better distributed (27.5% adequate vs. 17.5% for outdoor), reflecting greater spatial availability of commercial POIs than green space in the urban core.

```mermaid
quadrantChart
    title Shelter Priority Interpretation
    x-axis Low HRI --> High HRI
    y-axis Low Shelter --> High Shelter
    quadrant-1 Adequate
    quadrant-2 Safe
    quadrant-3 Watch
    quadrant-4 PRIORITY
```

| Quadrant | HRI | Shelter | Interpretation |
|----------|-----|---------|----------------|
| **PRIORITY** | High | Low | Needs immediate intervention |
| Adequate | High | High | Risk covered by existing shelters |
| Watch | Low | Low | Low risk but under-resourced |
| Safe | Low | High | No action needed |

---

## 10. Sensitivity Analysis

In a multiplicative model $\text{HRI} = H \times E \times V$, each component has unit elasticity — a 1% increase in any input produces exactly a 1% increase in $\text{HRI}$. A standard OAT perturbation chart would show three identical overlapping lines, which is uninformative.

Instead, we decompose the **empirical variance** of $\log(\text{HRI})$ across the 3,854 urban core blocks. Since $\log(\text{HRI}) = \log H + \log E + \log V$, the variance decomposes additively into main effects and covariance terms:

| Component | Contribution to $\text{Var}(\log \text{HRI})$ |
|-----------|-----------------------------------------------|
| Hazard ($H$) | 16.8% |
| **Exposure ($E$)** | **84.8%** |
| Vulnerability ($V$) | 22.8% |
| Cov($H$, $E$) | +12.7% |
| Cov($H$, $V$) | −16.9% |
| Cov($E$, $V$) | −20.2% |

![Sensitivity Analysis](sensitivity_oat.png)

**Exposure ($E$, population density) is the dominant empirical driver** of spatial $\text{HRI}$ variation. Hazard ($H$) contributes only 16.8% because UTCI is spatially smooth at ~1 km resolution — most urban blocks share similar thermal stress. Vulnerability ($V$) contributes 22.8%, limited by the modest spatial differentiation of GDP and nightlight within a single megacity. Negative covariance terms (e.g., Cov($H$,$V$) = −16.9%) reflect that wealthier areas tend to also be hotter (central business districts), partially cancelling each other out.

The scatter plot (b) confirms: $E$ shows a strong positive fan-shaped relationship with $\text{HRI}$, while $H$ and $V$ cluster in narrow bands with weak gradients.

---

## 11. Classification

**HRI** uses **Natural Breaks (Jenks)** classification with 7 classes, applied within the 3,854 urban core blocks. Within the urban core, the HRI distribution is substantially less skewed than across the full municipality (populated blocks only, no zero-population noise), so Jenks produces a more informative colour ramp.

**OHSPI and IHSPI** use the 4-category scheme described in Section 9.1 (Adequate / Low / Medium / High) rather than continuous classification. This is methodologically appropriate because negative values have a distinct policy meaning (shelter surplus) that should not be conflated with positive values on a continuous scale.

| HRI Class | Block count | Interpretation |
|-----------|------------|----------------|
| 1 (lowest) | 447 | Minimal risk |
| 2 | 1,374 | Low risk |
| 3 | 966 | Below average |
| 4 | 488 | Average |
| 5 | 316 | Above average |
| 6 | 171 | High risk |
| 7 (highest) | 92 | Critical — priority intervention |

---

## 12. Results

### Heat Risk Index ($\text{HRI}$) Spatial Distribution — Urban Core

Analysis scope: 3,854 inhabited blocks in 7 central Shanghai districts (黄浦 徐汇 长宁 静安 普陀 虹口 杨浦), total area ≈ 289 km².

Within the urban core, highest HRI concentrates in 黄浦区 (Huangpu) and parts of 杨浦区 (Yangpu) — areas combining high UTCI thermal load, dense population, and lower relative GDP. 静安区 (Jing'an), with its commercial core and higher nightlight intensity, shows lower Vulnerability and consequently lower HRI despite similar thermal conditions. 92 blocks (2.4%) fall in the highest HRI class and represent the most acute heat risk zones.

### Shelter Priority ($\text{OHSPI}$ and $\text{IHSPI}$) — Urban Core

$\text{OHSPI}$ (outdoor/green space priority): 8.4% of urban core blocks are High priority; 62.6% are Medium. The green space deficit is most acute in 黄浦区 and 虹口区, where historic high-density development left little room for parks.

$\text{IHSPI}$ (indoor/commercial priority): 27.5% of blocks are Adequate (surplus indoor shelter), primarily in 静安区 and 徐汇区 commercial corridors. 8.1% are High priority, concentrated in residential sub-districts with low POI density. The indoor pattern is more spatially dispersed than the outdoor pattern, reflecting commercial clustering effects.

### Dashboard

![Dashboard](https://raw.githubusercontent.com/Aurora-yang-git/HRI/refs/heads/cursor/shanghai-heat-risk-analysis-8327/output/maps/map_dashboard.png)

---

## 13. Limitations

1. **Population proxy.** OSM building footprints ≠ census-calibrated population. Industrial buildings inflate $PD_i$ in non-residential zones.

2. **Simplified Vulnerability ($V$).** Dropping age structure and house prices reduces the model from 5 to 3 sub-indicators. $PD_i$ as an age proxy lacks directional validity — dense areas may have *younger* populations (worker dormitories) rather than elderly concentrations.

3. **Static Hazard ($H$).** Monthly-mean UTCI from 2022 does not capture intra-day or event-scale variability. A heat-wave peak (e.g., July 2022, 40.9°C) would produce different spatial patterns.

4. **MAUP at block boundaries.** Hybrid spatial units (road polygons + fishnet grid) introduce a boundary artefact where unit type changes.

5. **Shelter capacity vs. presence.** POI count ≠ cooling capacity. A 200,000 m² mall and a 50 m² café both count as one POI.

---

## 14. Conclusion

This model operationalises the IPCC risk framework ($\text{Hazard} \times \text{Exposure} \times \text{Vulnerability}$) at the urban-block scale, using UTCI as a human-centred hazard metric instead of LST. By subtracting spatially explicit shelter indices ($\text{OHSI}$, $\text{IHSI}$) from normalised risk ($\text{HRI}^{\text{norm}}$), it produces **actionable priority maps** ($\text{OHSPI}$, $\text{IHSPI}$) that identify not just *where it is hot*, but *where it is hot and under-served by cooling resources*.

The multiplicative $\text{HRI}$ structure, while theoretically sound, is empirically dominated by Exposure ($E$, population density) due to its extreme spatial variance. Future work should incorporate real-time meteorological feeds and age-disaggregated population data to improve Hazard temporal resolution and Vulnerability specificity.

---

## References

- Yang, A. (2025). Mapping priority zones for urban heat mitigation in Shanghai: Heat risk vs. shelter provision. *Computers, Environment and Urban Systems*, 117, 102283. [doi:10.1016/j.compenvurbsys.2025.102283](https://www.sciencedirect.com/science/article/abs/pii/S0198971525000833)
- Yao, Y. et al. (2023). A 1-km global monthly UTCI dataset (GloUTCI-M). *Zenodo*. [doi:10.5281/zenodo.8310513](https://zenodo.org/records/8310513)
- Chen, Z. et al. (2021). An extended time series of harmonised nighttime light data (PCNL). *Zenodo*. [doi:10.5281/zenodo.7612389](https://zenodo.org/records/7612389)
- Kummu, M. et al. (2024). Gridded global datasets for GDP and HDI. *Zenodo*. [doi:10.5281/zenodo.13943886](https://zenodo.org/records/13943886)
- IPCC (2022). Climate Change 2022: Impacts, Adaptation and Vulnerability. AR6 WGII.
