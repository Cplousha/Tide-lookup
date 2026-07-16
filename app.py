"""
Tide Lookup
-----------
A Streamlit app that shows real tide predictions for U.S. coastal stations,
using NOAA's free public "Tides & Currents" API (no key or account needed).

What it does:
1. You type in a search term (like a city or beach name).
2. We ask NOAA for the list of all tide stations and find ones matching
   your search.
3. You pick the specific station you meant from a dropdown.
4. We fetch that station's high/low tide predictions for the next 2 days
   and display them in a table.
5. We also fetch a smoother set of predictions and draw a simple chart of
   the tide curve.

NOAA is the same data source many tide websites and apps are built on.
"""

# ---------------------------------------------------------
# 1. IMPORTS
# ---------------------------------------------------------
import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# ---------------------------------------------------------
# 2. PAGE SETUP
# ---------------------------------------------------------
st.set_page_config(page_title="Tide Lookup", page_icon="🌊")
st.title("🌊 Tide Lookup")
st.write(
    "Search for a coastal station and see its upcoming high/low tides, "
    "using live data from NOAA (the U.S. National Oceanic and Atmospheric Administration)."
)

# ---------------------------------------------------------
# 3. SESSION STATE
# ---------------------------------------------------------
# We store the list of matching stations here so it survives re-runs
# (Streamlit re-runs the script every time you click something).
if "matching_stations" not in st.session_state:
    st.session_state.matching_stations = None

# ---------------------------------------------------------
# 4. STEP 1: SEARCH FOR A STATION
# ---------------------------------------------------------
st.header("1. Find your station")

search_term = st.text_input("Search for a city, beach, or area name", value="Santa Monica")
search_clicked = st.button("Search stations")

if search_clicked:
    if not search_term.strip():
        st.error("Please enter something to search for.")
    else:
        try:
            # NOAA's metadata API gives us the full list of tide-prediction stations.
            # type=tidepredictions filters to stations that actually have tide predictions
            # (as opposed to only water temperature, currents, etc.).
            metadata_url = "https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations.json"
            response = requests.get(metadata_url, params={"type": "tidepredictions"}, timeout=15)
            data = response.json()

            all_stations = data.get("stations", [])

            # Simple, beginner-friendly search: keep stations whose name
            # contains the search term (case-insensitive).
            term_lower = search_term.strip().lower()
            matches = [s for s in all_stations if term_lower in s.get("name", "").lower()]

            if len(matches) == 0:
                st.error(f"No stations found matching '{search_term}'. Try a different city or area name.")
                st.session_state.matching_stations = None
            else:
                st.session_state.matching_stations = matches
                st.success(f"Found {len(matches)} matching station(s). Pick one below.")

        except requests.exceptions.Timeout:
            st.error("NOAA's station search took too long to respond. Please try again.")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to NOAA. Check your internet connection.")
        except Exception as e:
            st.error(f"Something went wrong while searching for stations: {e}")

# ---------------------------------------------------------
# 5. STEP 2: PICK A STATION AND SHOW ITS TIDES
# ---------------------------------------------------------
if st.session_state.matching_stations:
    st.header("2. Choose a station")

    stations = st.session_state.matching_stations
    # Build a friendly label like "Santa Monica, CA (9410840)" for each option.
    options = {f"{s['name']}, {s.get('state', '')} ({s['id']})": s["id"] for s in stations}

    chosen_label = st.selectbox("Matching stations", list(options.keys()))
    chosen_station_id = options[chosen_label]

    show_tides_clicked = st.button("Show tide predictions")

    if show_tides_clicked:
        try:
            today = datetime.now()
            begin_date = today.strftime("%Y%m%d")
            end_date = (today + timedelta(days=2)).strftime("%Y%m%d")

            # ---- Fetch the high/low tide events (a handful of rows) ----
            hilo_url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
            hilo_params = {
                "product": "predictions",
                "station": chosen_station_id,
                "begin_date": begin_date,
                "end_date": end_date,
                "datum": "MLLW",       # standard tide reference level
                "time_zone": "lst_ld", # station's local time, adjusted for daylight saving
                "units": "english",    # feet
                "interval": "hilo",    # only the high/low turning points
                "format": "json",
            }
            hilo_response = requests.get(hilo_url, params=hilo_params, timeout=15)
            hilo_data = hilo_response.json()

            if "error" in hilo_data:
                st.error(f"NOAA reported an error: {hilo_data['error'].get('message', 'Unknown error')}")
            elif "predictions" not in hilo_data:
                st.error("No tide prediction data was returned for this station.")
            else:
                # ---- Build a clean table of High/Low tide times ----
                rows = []
                for p in hilo_data["predictions"]:
                    tide_type = "High" if p["type"] == "H" else "Low"
                    rows.append({
                        "Date/Time": p["t"],
                        "Type": tide_type,
                        "Height (ft)": float(p["v"]),
                    })

                hilo_df = pd.DataFrame(rows)
                st.subheader(f"Upcoming high/low tides: {chosen_label}")
                st.dataframe(hilo_df, use_container_width=True)

                # ---- Fetch a smoother curve for charting ----
                curve_params = dict(hilo_params)
                curve_params["interval"] = "h"  # hourly points instead of just hi/lo
                curve_response = requests.get(hilo_url, params=curve_params, timeout=15)
                curve_data = curve_response.json()

                if "predictions" in curve_data:
                    curve_rows = [
                        {"Date/Time": p["t"], "Height (ft)": float(p["v"])}
                        for p in curve_data["predictions"]
                    ]
                    curve_df = pd.DataFrame(curve_rows)
                    curve_df["Date/Time"] = pd.to_datetime(curve_df["Date/Time"])
                    curve_df = curve_df.set_index("Date/Time")

                    st.subheader("Tide curve (next ~2 days)")
                    st.line_chart(curve_df["Height (ft)"])

        except requests.exceptions.Timeout:
            st.error("NOAA's tide data service took too long to respond. Please try again.")
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to NOAA. Check your internet connection.")
        except Exception as e:
            st.error(f"Something went wrong while fetching tide data: {e}")
