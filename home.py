import streamlit as st
import random
import requests
import folium
import openai
import pandas as pd
import geopandas as gpd
from streamlit_folium import folium_static
from shapely.geometry import Point
from scipy.spatial import KDTree
import numpy as np
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = openai.OpenAI(api_key=openai_api_key)

# Load Giga Geospatial Dataset (school_geolocation.csv)
SCHOOL_DATA_FILE = "school_geolocation.csv"

@st.cache_data
def load_geospatial_data():
    df = pd.read_csv(SCHOOL_DATA_FILE)

    # Convert DataFrame to GeoDataFrame
    gdf = gpd.GeoDataFrame(
        df,
        geometry=[Point(xy) for xy in zip(df["longitude"], df["latitude"])],
        crs="EPSG:4326"  # WGS 84 coordinate system
    )
    
    return gdf

# Load school data
giga_data = load_geospatial_data()

# Extract school names and coordinates
nodes = giga_data["school_name"].tolist()
node_locations = {row["school_name"]: [row.latitude, row.longitude] for _, row in giga_data.iterrows()}

# Build a spatial tree for fast nearest-neighbor lookup
school_coords = giga_data[["latitude", "longitude"]].values
school_names = giga_data["school_name"].tolist()
school_tree = KDTree(school_coords)

# AI-Powered Query Processing (Updated for OpenAI >=1.0.0)
def process_query(query, location):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are an AI expert in geospatial networks assisting schools in {location}."},
                {"role": "user", "content": query}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI Processing Failed: {e}"

# Find the Closest School Based on Query Location
def find_best_node(lat, lon):
    _, idx = school_tree.query([lat, lon])
    return school_names[idx]

# Draw Geospatial Network
def draw_network():
    m = folium.Map(location=[0, 0], zoom_start=2)  # Default to world map

    for node, loc in node_locations.items():
        folium.Marker(
            location=[loc[0], loc[1]],  # Correct order: lat, lon
            tooltip=node,
            icon=folium.Icon(color="blue")
        ).add_to(m)

    folium_static(m)

# Streamlit UI
st.title("AI-Powered Geospatial Mesh Network 🌍")
st.title("Connnect With World without Internet")
st.write("This project simulates **AI-powered query routing** in a **real-world geospatial network** using Giga data.")

query = st.text_area("Enter your question:")
lat = st.number_input("Enter your latitude:", value=30.3753)  # Default: Pakistan
lon = st.number_input("Enter your longitude:", value=69.3451)

if st.button("Submit Query"):
    if query:
        st.write("### Step 1: AI Processing")
        best_node = find_best_node(lat, lon)
        processed_query = process_query(query, best_node)
        st.success(processed_query)

        st.write("### Step 2: Geospatial Routing")
        st.info(f"Query is routed to: {best_node} (Location: {node_locations[best_node]})")

        st.write("### Step 3: Network Visualization")
        draw_network()

        st.write("### Step 4: AI Response from Node")
        st.success(f"Response from {best_node}: {processed_query}")
    else:
        st.warning("Please enter a query.")
