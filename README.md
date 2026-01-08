# Visualising the "Ground Truth": Investigating the Spatial Divergence of Deprivation and the Night-Time Economy in Bristol

**UWE Bristol – MSc Data Science**
**Module:** UFCF9Y-60-M CSCT Masters Project
**Student ID:** 25005629
**Academic Year:** 2025/2026

## Project Overview

This project investigates the spatial drivers of crime in Bristol by developing an interactive data science artifact. Motivated by the limitations of static police reporting—specifically the **Modifiable Areal Unit Problem (MAUP)**—the project constructs a Python-based dashboard to analyse ten months of incident data from January to October 2025.

By integrating police logs, socioeconomic indices (IMD), and commercial venue data, the study moves beyond simple aggregate counting to reveal the complex, non-linear relationship between urban structure and criminality. It specifically explores the "Rank Discordance" between residential deprivation and the Night-Time Economy (NTE).

## Objectives

* **Data Integration:** Construct a unified dataset merging police crime records with socioeconomic statistics (IMD) and commercial venue locations.
* **Correlation Modelling:** Quantify the statistical link between deprivation domains (Income, Employment) and crime rates.
* **Spatial Analysis:** Utilise dual-layer mapping (Choropleth vs. Heatmap) to distinguish between poverty-driven residential crime and opportunity-driven commercial crime.
* **Artifact Development:** Develop an interactive Streamlit dashboard to enable dynamic filtering and "Ground Truth" visualisation.
* **Rank Discordance Evaluation:** Identify and explain anomalies where high crime rates occur in low-deprivation areas.

## Repository Contents

* **`app.py`**
  The main Streamlit application script containing the dashboard logic, visualisation engine, and reactive filtering pipeline.

* **`data_processing_pipeline.ipynb`**
  Jupyter Notebook used for data cleaning, aggregation, and the calculation of crime rates per 1,000 residents.

* **`README.md`**
  Project documentation (this file).

* **`requirements.txt`**
  List of Python dependencies required to run the dashboard locally.

## Interactive Dashboard

The artifact is built as a multi-tab web application featuring:
* **Spatial Analysis Tab:** Dual-layer maps allowing users to toggle between Administrative Views (Choropleth) and Density Views (Heatmaps).
* **Statistical Correlation Tab:** Interactive Pearson Correlation Matrix for socioeconomic variables.
* **Data Explorer Tab:** Raw data interface for granular inspection of incident logs.

**[Link to Live Dashboard](https://bristol-crime-analysis-aadr3qbu63yexu6yvpzpqm.streamlit.app/)**

## Data Availability

Due to GitHub file size limitations, raw datasets are not included in this repository. Data were obtained from the following open-access sources:

* **Police.uk Data Downloads**
  Anonymised crime logs and incident data.
  [https://data.police.uk/](https://data.police.uk/)

* **Open Data Bristol (IMD 2019/2025)**
  Indices of Multiple Deprivation scores and LSOA boundaries.
  [https://www.bristol.gov.uk/files/documents/10436-deprivation-in-bristol-2025/file](https://www.bristol.gov.uk/files/documents/10436-deprivation-in-bristol-2025/file)

* **Geo spatial data**
  Full-resolution vector polygons (GeoJSON) for Lower-layer Super Output Areas (2021 Census)
  [https://geoportal.statistics.gov.uk/datasets/ons::lower-layer-super-output-areas-december-2021-boundaries-ew-bsc-v4-2/about](https://geoportal.statistics.gov.uk/datasets/ons::lower-layer-super-output-areas-december-2021-boundaries-ew-bsc-v4-2/about)

* **Food Standards Agency (FSA)**
  Locations of licensed premises (Pubs, Clubs, Restaurants) used to proxy the Night-Time Economy.
  [https://opendata.bristol.gov.uk/datasets/7d0994dded2348d5aff6d419b0c76bb9_0/explore](https://opendata.bristol.gov.uk/datasets/7d0994dded2348d5aff6d419b0c76bb9_0/explore)

All data sources are publicly available and used in aggregated form only.

## Methodology Summary

1. **Data Integration**
   Crime records were spatially joined to LSOA boundaries. A "Crime Rate per 1,000" metric was calculated to normalize for population density.

2. **Socioeconomic Correlation**
   Pearson correlation coefficients ($r$) were calculated to test Social Disorganization Theory against the Bristol dataset ($r \approx 0.36$).

3. **Dual-Layer Visualisation**
   * *Layer 1 (Choropleth):* Visualises administrative risk based on census boundaries.
   * *Layer 2 (KDE Heatmap):* Visualises continuous spatial density to overcome the MAUP and reveal "Edge Effects" (e.g., the Henbury/Brentry cluster).

4. **Rank Discordance Analysis**
   A comparative analysis of the "Top 10 Most Deprived" vs. "Top 10 High-Crime" areas was conducted to isolate the impact of the Night-Time Economy.

## How to Run

### Requirements
* Python 3.9+
* Streamlit

### Install Dependencies
```bash
pip install -r requirements.txt
