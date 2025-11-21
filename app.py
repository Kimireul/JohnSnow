import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from branca.element import Template, MacroElement
from streamlit_folium import st_folium
from pyproj import Transformer

# -----------------------------------------
# 1. STREAMLIT CONFIGURATION
# -----------------------------------------
st.set_page_config(page_title="Cholera Death Map", layout="wide")
st.title("Cholera Death Dashboard")

# -----------------------------------------
# 2. LOAD CSV DATA
# -----------------------------------------
pd_deaths = pd.read_csv("Cholera_Deaths.csv")
pd_pumps = pd.read_csv("Pumps.csv")

# -----------------------------------------
# 3. REPROJECT FROM EPSG:27700 → EPSG:4326
# -----------------------------------------
transformer = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

def reproject(df):
    lons = []
    lats = []
    for x, y in zip(df["X"], df["Y"]):
        lon, lat = transformer.transform(x, y)
        lons.append(lon)
        lats.append(lat)
    df["lon"] = lons
    df["lat"] = lats
    return df

pd_deaths = reproject(pd_deaths)
pd_pumps = reproject(pd_pumps)

# -----------------------------------------
# 4. SUMMARY STATISTICS
# -----------------------------------------
total_deaths = len(pd_deaths)
death_counts = pd_deaths.groupby(["X", "Y"]).size()
max_death_same_location = death_counts.max()

st.metric("Total Cholera Deaths", total_deaths)
st.metric("Maximum Deaths at One Location", int(max_death_same_location))

# -----------------------------------------
# 5. CREATE FOLIUM MAP
# -----------------------------------------
center_lat = pd_deaths["lat"].mean()
center_lon = pd_deaths["lon"].mean()

m = folium.Map(location=[center_lat, center_lon], zoom_start=16)

# -----------------------------------------
# 6. ADD DEATH POINTS
# -----------------------------------------
deaths_layer = folium.FeatureGroup(name="Cholera Deaths")
for _, row in pd_deaths.iterrows():
    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=3,
        color="red",
        fill=True,
        fill_opacity=0.8
    ).add_to(deaths_layer)
deaths_layer.add_to(m)

# -----------------------------------------
# 7. ADD WATER PUMPS
# -----------------------------------------
pumps_layer = folium.FeatureGroup(name="Water Pumps")
for _, row in pd_pumps.iterrows():
    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup="Water Pump",
        icon=folium.Icon(color="blue", icon="tint", prefix="fa")
    ).add_to(pumps_layer)
pumps_layer.add_to(m)

# -----------------------------------------
# 8. LAYER CONTROL
# -----------------------------------------
folium.LayerControl().add_to(m)

# -----------------------------------------
# 9. TITLE + LEGEND
# -----------------------------------------
template = """
{% macro html(this, kwargs) %}
<div style="
    position: fixed;
    top: 10px;
    left: 50%;
    transform: translateX(-50%);
    z-index:9999;
    background-color:white;
    padding:10px;
    border:2px solid grey;
    border-radius:5px;
    font-size:16px;
    font-weight:bold;
    ">
    CHOLERA DEATH MAP
</div>

<div style="
    position: fixed;
    bottom: 50px;
    left: 10px;
    z-index:9999;
    background-color:white;
    padding:10px;
    border:2px solid grey;
    border-radius:5px;
    font-size:14px;
    ">
    <i class="fa fa-circle" style="color:red;"></i> Cholera Deaths<br>
    <i class="fa fa-tint" style="color:blue;"></i> Water Pumps
</div>
{% endmacro %}
"""

macro = MacroElement()
macro._template = Template(template)
m.get_root().add_child(macro)

# -----------------------------------------
# 10. DISPLAY MAP
# -----------------------------------------
st.subheader("Interactive Cholera Map")
st_folium(m, width=1000, height=600)
