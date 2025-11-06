# ---- Base image ----
FROM python:3.10-slim

# ---- Set working directory ----
WORKDIR /app

# ---- Install system dependencies ----
# Required for geopandas, rasterio, fiona, shapely, etc.
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    python3-gdal \
    && rm -rf /var/lib/apt/lists/*

# ---- Copy project files ----
COPY requirements.txt .
COPY main.py .

# ---- Install Python dependencies ----
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# ---- Expose Streamlit default port ----
EXPOSE 8501

# ---- Run Streamlit ----
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
