**Key Variables for LCZ-Based Heat Risk Index (HRI) Modeling**

To construct a GIS-based urban heat risk model, this study integrates the **Local Climate Zone (LCZ) framework** with a **Heat Risk Index (HRI)** approach. Only the variables that directly influence urban heat exposure and human health risk are included.

The variables can be grouped into **three primary components: thermal hazard, population exposure, and environmental modifiers**.

---

**1. Thermal Hazard Variables (Core HRI Indicators)**

Thermal hazard represents the **intensity of heat stress in the environment**.  
The main indicator used is the **Heat Index**, which reflects the combined effect of air temperature and humidity on perceived human heat stress.

**Heat Index (HI)**

The **Heat Index (HI)** is calculated using:

- **Air temperature (T)**
- **Relative humidity (RH)**

The Heat Index estimates the **apparent temperature perceived by the human body** under humid conditions.

Typical simplified formula:

[  
HI = f (T, RH)  
]

Where:

- **T** = air temperature (°C or °F)
- **RH** = relative humidity (%)

Higher humidity reduces the body’s ability to cool through sweating, increasing heat stress risk.

Heat Index values are commonly classified into risk categories such as:

|**Heat Index Level**|**Risk Level**|
|---|---|
|< 27°C|Low risk|
|27–32°C|Caution|
|32–41°C|Extreme caution|
|41–54°C|Danger|
|> 54°C|Extreme danger|

The Heat Index therefore serves as the **primary hazard indicator in the Heat Risk Index (HRI)**.

---

**2. Environmental Spatial Modifiers (LCZ-Based Factors)**

The **Local Climate Zone (LCZ)** framework is used to represent the **urban spatial structure** that modifies heat intensity.

Instead of using all LCZ variables, the model focuses on the factors that most strongly influence urban thermal conditions:

**2.1 Building Density**

Represents the concentration of built structures within an area.

Higher building density:

- Traps heat
- Reduces ventilation
- Increases nighttime heat retention

**2.2 Impervious Surface Ratio**

Percentage of surfaces such as asphalt, concrete, and rooftops.

High impervious coverage:

- Increases solar heat absorption
- Reduces evaporative cooling

**2.3 Vegetation Cover (NDVI)**

Vegetation density measured through remote sensing.

Vegetation contributes to:

- Evapotranspiration cooling
- Shading effects
- Reduced surface temperatures

**2.4 Water Bodies**

Presence of rivers, lakes, or canals.

Water surfaces help regulate temperature through:

- Thermal inertia
- Evaporative cooling.

These variables allow LCZ to function as a **spatial correction layer** that modifies the intensity of heat hazards.

---

**3. Population Exposure Variables**

Population exposure reflects **how many people are present in areas experiencing heat stress**.

Only the most essential indicator is required:

**Population Density**

Population density indicates the potential number of individuals exposed to heat hazards within a given spatial unit.

Higher population density increases the **overall heat risk level**, even if environmental heat conditions remain constant.

In real-time applications, exposure can also be approximated through:

- Mobility data
- Activity hotspots
- Transportation nodes.

---

**4. Heat Risk Index (HRI) Construction**

The **Heat Risk Index (HRI)** integrates the three components described above.

Conceptually:

[  
HRI = f (Hazard, Exposure, Environmental\ Modifiers)  
]

Where:

- **Hazard** = Heat Index (temperature + humidity)
- **Exposure** = population density
- **Environmental modifiers** = LCZ-related spatial factors

The index allows the system to produce **spatial heat risk maps** at high resolution.

Areas with:

- High Heat Index values
- Dense built environments
- High population density

Will receive the **highest heat risk classification**.

---

**5. Application in Real-Time Urban Heat Risk Mapping**

Within a real-time urban heat monitoring system, the variables are used as follows:

- **Heat Index (HI):** real-time meteorological input
- **LCZ spatial factors:** static background layer derived from GIS and remote sensing
- **Population density:** exposure indicator

The final HRI layer can then support:

- Real-time heat risk visualization
- Identification of high-risk urban zones
- Public heat warning systems
- Guidance toward cooling shelters or shaded routes.

---

Lcz+heva

---

**LCZ****–GIS Heat Risk Modeling Framework (Summary)**

**1. Local Climate Zone (LCZ) Framework**

The **Local Climate Zone (LCZ)** framework, proposed by Stewart Iain D. and Timothy R. Oke, is widely used in urban climate research to classify cities into zones with similar **surface structure, land cover, and thermal behavior**.

LCZ divides urban environments into **17 standardized categories**, including:

- **10 built types** (e.g., compact high-rise, compact mid-rise, open low-rise)
- **7 natural types** (e.g., dense trees, water, low plants, bare soil)

Each LCZ type represents a **distinct urban morphology and thermal environment**, influencing factors such as:

- Surface temperature
- Heat storage capacity
- Ventilation potential
- Human heat exposure

Because LCZ captures **spatial heterogeneity of urban environments**, it is widely used in GIS-based urban heat island and heat risk studies.

---

**2. Key GIS Factors Required for LCZ-Based Heat Risk Analysis**

To construct an LCZ-based heat risk model within a GIS system, previous studies (e.g., urban heat island research in Chinese megacities) commonly integrate several categories of spatial data.

**2.1 Urban Morphology Factors**

These variables describe the **three-dimensional structure of the built environment**.

Typical indicators include:

- **Building height**
- **Building density**
- **Floor area ratio**
- **Sky view factor**
- **Street canyon geometry**
- **Impervious surface ratio**

These factors influence:

- Urban heat storage
- Radiation trapping
- Ventilation conditions

For example, compact high-rise zones often retain more heat due to reduced airflow and higher surface heat capacity.

---

**2.2 Land Cover and Surface Properties**

Land cover significantly affects urban thermal conditions.

Common variables include:

- **vegetation cover**
- **tree canopy density**
- **water bodies**
- **bare soil**
- **impervious surfaces**

Vegetation and water bodies generally contribute to **cooling effects through evapotranspiration**, while impervious surfaces tend to increase heat accumulation.

Satellite data (e.g., **NDVI**) is often used to quantify vegetation coverage.

---

**2.3 Thermal Environment Indicators**

Thermal indicators represent the **hazard component** of heat risk.

Typical variables include:

- **Land Surface Temperature (LST)** derived from satellite imagery
- **Air temperature**
- **Relative humidity**
- **Heat index / apparent temperature**

In dynamic heat risk systems, these indicators can be updated using **real-time weather data**.

---

**2.4 Population Exposure Factors**

Exposure represents the **degree to which people are present in high-temperature environments**.

Typical indicators include:

- **population density**
- **human mobility patterns**
- **crowd density in public areas**
- **land use intensity**

In smart city applications, exposure may be estimated using:

- Mobile location data
- Transportation data
- Urban activity centers.

---

**2.5 Vulnerability Indicators**

Vulnerability represents **how susceptible populations are to heat-related health impacts**.

Common indicators include:

- Proportion of elderly population
- Proportion of children
- Health status indicators
- Socioeconomic conditions
- Housing quality
- Access to air conditioning

These variables are often used to adjust heat risk levels across different neighborhoods.

---

**2.6 Adaptability and Infrastructure**

Adaptability refers to **the ability of individuals or communities to cope with heat stress**.

Typical indicators include:

- Cooling centers
- Medical facilities
- Public shelters
- Green spaces
- Accessibility to shaded routes

In GIS analysis, these facilities can be represented through **network accessibility analysis**.

---

**3. Integrating LCZ with the HEVA Heat Risk Model**

Many recent urban heat risk studies combine the **LCZ spatial framework** with the **HEVA model (Hazard****–Exposure–Vulnerability–Adaptability)**.

In this integrated framework:

|**Component**|**Meaning**|**Data Sources**|
|---|---|---|
|Hazard|Thermal environment intensity|temperature, humidity, LST|
|Exposure|Population presence in hot areas|population density, mobility|
|Vulnerability|Sensitivity of populations|age structure, health, socioeconomic status|
|Adaptability|Capacity to respond to heat|cooling centers, medical access|

LCZ functions as a **spatial modifier** that influences the distribution of hazard and exposure by representing the underlying urban morphology.

---

**4. Application to Real-Time Urban Heat Risk Systems**

In a smart-city heat risk monitoring system, LCZ is typically used as a **background spatial layer rather than a real-time variable**.

The overall heat risk calculation can be conceptualized as:

**Real-time meteorological data** **× LCZ spatial correction × population exposure × vulnerability factors**

This approach allows the system to generate **high spatial and temporal resolution heat risk maps**.

For example:

- Compact high-rise LCZ zones may receive **higher risk weights**
- Green areas or water bodies may receive **lower risk weights**

By integrating LCZ with dynamic weather data, GIS platforms can produce **more accurate real-time heat risk assessments**, which can support:

- Heat warning systems
- Route planning for safer outdoor movement
- Identification of cooling shelters and emergency facilities.