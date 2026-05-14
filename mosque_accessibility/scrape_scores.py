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
    if 'geocode_method' not in df.columns: df['geocode_method'] = None

# --- GEOCODING SETUP ---
GEOCODER_URL = "https://geocoding.geo.census.gov/geocoder/locations/address"

geolocator = Nominatim(user_agent="mosque_geocoder")
nominatim_geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.0)

def build_address(row):
    parts = [str(row['Street']), str(row['City']), str(row['State'])]
    return ', '.join(p for p in parts if p and p.lower() != 'nan')

def geocode_census(row):
    """Primary: US Census Geocoder."""
    street = str(row.get('Street', '') or '').strip()
    city = str(row.get('City', '') or '').strip()
    state = str(row.get('State', '') or '').strip()
    zip_code = str(row.get('ZCTA', '') or '').strip()

    if not street or street.lower() == 'nan':
        return None, None

    params = {
        'street': street,
        'city': city,
        'state': state,
        'zip': zip_code,
        'benchmark': 'Public_AR_Current',
        'format': 'json'
    }

    try:
        response = requests.get(GEOCODER_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        matches = data.get('result', {}).get('addressMatches', [])
        if matches:
            coords = matches[0].get('coordinates', {})
            return coords.get('y'), coords.get('x')
        return None, None
    except Exception as e:
        print(f"  Census Geocoder error: {e}")
        return None, None

def geocode_nominatim(row):
    """Fallback: Nominatim (OpenStreetMap)."""
    addr = build_address(row)
    if not addr:
        return None, None
    try:
        location = nominatim_geocode(addr)
        if location:
            return location.latitude, location.longitude
        return None, None
    except Exception as e:
        print(f"  Nominatim error: {e}")
        return None, None

def geocode_address(row):
    """Try Census Geocoder first, fall back to Nominatim."""
    if pd.notna(row['Latitude']) and pd.notna(row['Longitude']):
        return row['Latitude'], row['Longitude'], row.get('geocode_method')

    lat, lon = geocode_census(row)
    if lat is not None:
        print(f"   Census: {str(row['Street'])[:40]} → ({lat}, {lon})")
        return lat, lon, 'census_geocoder'

    time.sleep(1.0)
    lat, lon = geocode_nominatim(row)
    if lat is not None:
        print(f"   Nominatim: {str(row['Street'])[:40]} → ({lat}, {lon})")
        return lat, lon, 'nominatim'

    return None, None, None

# --- GEOCODING LOOP ---
print("Geocoding addresses to Latitude/Longitude...")
census_count = 0
nominatim_count = 0
missing_count = 0

for index, row in df.iterrows():
    if pd.notna(row['Latitude']) and pd.notna(row['Longitude']):
        continue

    lat, lon, method = geocode_address(row)
    df.at[index, 'Latitude'] = lat
    df.at[index, 'Longitude'] = lon
    df.at[index, 'geocode_method'] = method

    if method == 'census_geocoder':
        census_count += 1
    elif method == 'nominatim':
        nominatim_count += 1
    else:
        missing_count += 1

    time.sleep(0.5)

df.to_csv(output_file, index=False)
print(f"Geocoding complete | Census: {census_count} | Nominatim: {nominatim_count} | Missing: {missing_count}")

# --- WALKSCORE SCRAPE ---
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