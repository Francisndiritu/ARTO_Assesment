import streamlit as st
import geopandas as gpd
import pandas as pd
import rasterio
import rasterio.mask
from shapely.geometry import mapping
import matplotlib.pyplot as plt
import numpy as np
import os
import requests
from io import BytesIO
from zipfile import ZipFile

st.set_page_config(page_title="Guinea Rainfall & Population 2025", layout="wide")

st.title("Guinea 2025 Population and September Rainfall Analysis")

# -------------------------------------------------------------
# 1️ SETUP PATHS AND DOWNLOAD CHIRPS DATA
# ------------------------------------------------------------------------
chirps_url = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/africa_monthly/tifs/chirps-v2.0.2025.09.tif"
chirps_path = "data/chirps-v2.0.2025.09.tif"

os.makedirs("data", exist_ok=True)

if not os.path.exists(chirps_path):
    st.info("Downloading CHIRPS September 2025 raster ...")
    r = requests.get(chirps_url, stream=True)
    if r.status_code == 200:
        with open(chirps_path, "wb") as f:
            f.write(r.content)
        st.success("CHIRPS data downloaded successfully.")
    else:
        st.error("Failed to download CHIRPS raster.")
else:
    st.success("CHIRPS raster already available locally.")

# ------------------------------------------------------------------
# 2️ READ SHAPEFILE AND POPULATION DATA
# ------------------------------------------------------------
shapefile_path = "data/who_shapefile_gin_adm2_issues.gpkg"
pop_csv_path = "data/gin_pop_2025.csv"

st.info("Reading shapefile and population data ...")
gdf = gpd.read_file(shapefile_path)
pop_df = pd.read_csv(pop_csv_path)

st.write("Shapefile and Population Data loaded successfully.")
st.write("Shapefile columns:", list(gdf.columns))
st.write("Population Data columns:", list(pop_df.columns))

# ---------------------------------------------
# 3️ VALIDATE & FIX SHAPEFILE GEOMETRIES
# ------------------------------------------------------------------------------
st.info("Validating and fixing geometries.")
gdf = gdf[gdf.is_valid]  # Drop invalid geometries
gdf["geometry"] = gdf["geometry"].buffer(0)  # Fix minor geometry errors
st.success("Geometries validated and fixed.")

# -----------------------------------------------
# 4️  CLEAN AND ALIGN ADMINISTRATIVE NAMES
# ------------------------------------------------------------------------------
st.info("Cleaning and aligning administrative names.")

def clean_names(x):
    return str(x).strip().lower().replace("-", " ").replace("_", " ")

# Assuming 'ADM2_EN' or similar field in shapefile and 'adm2_name' in population CSV
shapefile_name_col = "adm2" if "adm2" in gdf.columns else gdf.columns[0]
pop_name_col = "adm2" if "adm2" in pop_df.columns else pop_df.columns[0]

gdf["adm2_clean"] = gdf[shapefile_name_col].apply(clean_names)
pop_df["adm2_clean"] = pop_df[pop_name_col].apply(clean_names)

# --------------------------------------------------------------
# 5️ JOIN POPULATION DATA TO SHAPEFILE
# ----------------------------------------------------------------------
st.info("Joining population data to shapefile ...")
gdf = gdf.merge(pop_df, on="adm2_clean", how="left")

if "pop" not in gdf.columns:
    # Rename possible population column
    pop_col = [c for c in gdf.columns if "pop" in c.lower()][0]
    gdf.rename(columns={pop_col: "pop_2025"}, inplace=True)

st.success("Population data joined to shapefile.")

# ----------------------------------------
# 6️ EXTRACT RAINFALL FROM CHIRPS RASTER BY ADM2
# ------------------------------------------------------
st.info("Extracting total rainfall (September 2025) per administrative unit ...")

with rasterio.open(chirps_path) as src:
    affine = src.transform
    array = src.read(1)

    # Mask out invalid data
    array = np.where(array < 0, np.nan, array)

    rainfall_vals = []
    for geom in gdf.geometry:
        try:
            out_image, out_transform = rasterio.mask.mask(src, [mapping(geom)], crop=True)
            out_image = np.where(out_image < 0, np.nan, out_image)
            rainfall_vals.append(np.nanmean(out_image))
        except Exception:
            rainfall_vals.append(np.nan)

gdf["rainfall_sep2025"] = rainfall_vals
st.success("Rainfall extracted successfully.")

# ------------------------------------------------------------------------------
# 7️ PRODUCE MAPS
# ------------------------------------------------------------------------------

st.subheader(" Map 1: Population Distribution (2025)")
fig1, ax1 = plt.subplots(figsize=(8, 8))
gdf.plot(column="pop", ax=ax1, legend=True, cmap="YlOrRd", edgecolor="black")
ax1.set_title("Population Distribution (2025)", fontsize=14)
ax1.axis("off")
st.pyplot(fig1)

# ------------Save the Output------------

pop_map_path = "Output/population_distribution_2025.png"
fig1.savefig(pop_map_path, dpi=300, bbox_inches="tight")
st.success(f"Population map saved in: {pop_map_path}")
# -------------end----------------------

st.subheader("Map 2: Total Rainfall (September 2025)")
fig2, ax2 = plt.subplots(figsize=(8, 8))
gdf.plot(column="rainfall_sep2025", ax=ax2, legend=True, cmap="Blues", edgecolor="black")
ax2.set_title("Total Rainfall (September 2025)", fontsize=14)
ax2.axis("off")
st.pyplot(fig2)

# --- Save Map 2 ---
rainfall_map_path = "Output/total_rainfall_sep2025.png"
fig2.savefig(rainfall_map_path, dpi=300, bbox_inches="tight")
st.success(f"Rainfall map saved in: {rainfall_map_path}")

# ------------------------------------------------------------------------------
# 8️EXPORT CLEANED SHAPEFILE WITH POPULATION AND RAINFALL
# ------------------------------------------------------------------------------
output_path = "Output/guinea_cleaned_results.gpkg"
gdf.to_file(output_path, driver="GPKG")

st.success("Final cleaned shapefile exported successfully.")
st.write("Output saved to:", output_path)


# ------------------------------------------------------------------------------
# 9️DISPLAY SAMPLE DATA
# ------------------------------------------------------------------------------
st.subheader("Sample of Final Data")
st.dataframe(gdf[["adm2_clean", "pop", "rainfall_sep2025"]].head())

# ------------------------------------------------------
# ------------------------------------------------------

st.set_page_config(page_title="View Cleaned Shapefile", layout="wide")
st.title("View Cleaned Guinea Shapefile Attributes")

# --- Load cleaned shapefile ---
file_path = "Output/guinea_cleaned_results.gpkg"

try:
    gdf = gpd.read_file(file_path)
    st.success("Cleaned shapefile loaded successfully.")
except Exception as e:
    st.error(f"Error loading shapefile: {e}")
    st.stop()

# --- Drop geometry for table view ---
df = pd.DataFrame(gdf.drop(columns="geometry"))

# --- Basic info ---
st.write(f"**Total Administrative Units:** {len(df)}")
st.write("**Columns available:**", list(df.columns))

# --- Display attribute table ---
st.dataframe(df)
# --- Download/Save Locally as CSV ---
csv_path = "Output/guinea_results_2025.csv"