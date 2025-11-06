#Guinea 2025 Population and Rainfall Analysis

This Streamlit app analyzes Guinea’s 2025 population distribution and September rainfall 
(CHIRPS data) at the administrative level. It downloads CHIRPS raster data, validates and 
cleans shapefiles, merges population data, extracts mean rainfall per district, and visualizes
results through interactive maps. The final cleaned dataset is exported as a GeoPackage and CSV
file inside the Output/ folder.

#Approach

Data Download: Automatically fetches CHIRPS September 2025 rainfall raster/It also checks 
if the data is available locally.

Data Cleaning: Fixes invalid geometries and standardizes administrative names.

Join & Analysis: Merges population data with rainfall means extracted per ADM2 boundary using rasterio.mask.

Visualization: Generates thematic maps for population and rainfall using matplotlib.

Output: Exports a cleaned GeoPackage (guinea_cleaned_results.gpkg) and attribute table CSV (guinea_results_2025.csv).