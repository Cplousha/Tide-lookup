Tide Lookup

A Streamlit app that shows real tide predictions for U.S. coastal stations, using NOAA's free public Tides & Currents API — no API key or account required.

## What it does
1. You search for a station by city/beach/area name (e.g. "Santa Monica").
2. It shows matching NOAA tide stations to choose from.
3. It fetches and displays the upcoming high/low tide times and heights.
4. It draws a simple chart of the predicted tide curve for the next ~2 days.

## Run it locally
pip install -r requirements.txt
streamlit run app.py

## Tech stack
- Streamlit — web app framework
- pandas — data handling
- requests — for calling the API
- NOAA Tides & Currents — official U.S. government tide data, free, no key needed
