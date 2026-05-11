import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random
import os
import re
import urllib.parse
from geopy.geocoders import Nominatim 
from geopy.extra.rate_limiter import RateLimiter


input_file = '../data/CLEAN_USMosqueDatabase(Physical-Spatial).csv'
output_file = '../data/mosques_scores.csv'

if os.path.exists(output_file):
    print(f"Found existing progress in {output_file}.")
    df = pd.read_csv(output_file)
else:
    print(f"No existing progress found. Loading data from {input_file}.")
    df = pd.read_csv(input_file, dtype={'Mosque_ID': str, 'ZCTA': str})
    df.columns = df.columns.str.strip()
    df = df.dropna(subset=['Mosque_ID']).reset_index(drop=True)
    if 'Walk_score' not in df.columns: df['Walk_score'] = None
    if 'Transit_score' not in df.columns: df['Transit_score'] = None
    if 'Latitude' not in df.columns: df['Latitude'] = None
    if 'Longitude' not in df.columns: df['Longitude'] = None

# Initialize Geocoder
geolocator = Nominatim(user_agent="mosque_geocoder")
geocode_service = RateLimiter(geolocator.geocode, min_delay_seconds=1.0)


def build_address(row):
    parts = [str(row['Street']), str(row['City']), str(row['State'])]
    return ', '.join(p for p in parts if p and p.lower() != 'nan')


def geocode_address(row):
    if pd.notna(row['Latitude']) and pd.notna(row['Longitude']):
        return row['Latitude'], row['Longitude']

    addr = build_address(row)
    if not addr:
        return None, None

    try:
        location = geocode_service(addr)
        if location:
            print(f"   Geocoded: {addr[:40]} → ({location.latitude}, {location.longitude})")
            return location.latitude, location.longitude
        return None, None
    except Exception as e:
        print(f"Geocoding error for '{addr}': {e}")
        return None, None


print("Geocoding addresses to Latitude/Longitude...")
for index, row in df.iterrows():
    if pd.notna(row['Latitude']) and pd.notna(row['Longitude']):
        continue
    lat, lon = geocode_address(row)
    df.at[index, 'Latitude'] = lat
    df.at[index, 'Longitude'] = lon

df.to_csv(output_file, index=False)
print("Geocoding complete")


def get_walkscore_data(address_string):
    if pd.isna(address_string) or address_string == "":
        return None, None

    address_string = str(address_string).replace("/", " ")
    encoded_address = urllib.parse.quote(address_string)
    url = f"https://www.walkscore.com/score/{encoded_address}"
    print(url)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            walk_score = None
            transit_score = None

            ws_img = soup.find('img', src=re.compile(r'badge/walk/score'))
            if ws_img:
                match = re.search(r'score/(\d+)\.', ws_img['src'])
                if match:
                    walk_score = match.group(1)

            ts_img = soup.find('img', src=re.compile(r'badge/transit/score'))
            if ts_img:
                match = re.search(r'score/(\d+)\.', ts_img['src'])
                if match:
                    transit_score = match.group(1)

            return walk_score, transit_score
        else:
            return None, None
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None, None


print("Starting WalkScore scrape...")

for index, row in df.iterrows():
    if pd.notna(row['Walk_score']):
        continue

    addr = build_address(row)

    if addr:
        w_score, t_score = get_walkscore_data(addr)

        df.at[index, 'Walk_score'] = w_score
        df.at[index, 'Transit_score'] = t_score

        print(f"{index+1}/{len(df)}: {addr[:40]} - Walk: {w_score}, Transit: {t_score}")

        time.sleep(random.uniform(1.1, 2.1))
    else:
        print(f"[{index+1}/{len(df)}] No address, skipping.")

    if (index + 1) % 100 == 0:
        print(f"Saving progress at row {index+1}...")
        df.to_csv(output_file, index=False)

df.to_csv(output_file, index=False)
print("Final file saved.")