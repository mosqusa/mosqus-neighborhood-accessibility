import os
import pandas as pd
from census import Census
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
CENSUS_API_KEY = os.environ["CENSUS_API_KEY"]
INPUT_FILE = "../data/mosques_scores.csv"
OUTPUT_FILE = "../data/mosques_socioeconomic.csv"
YEAR = 2024 # Using 2024 ACS 5-Year estimates (most recent data)

c = Census(CENSUS_API_KEY)

print("Loading dataset")
df = pd.read_csv(INPUT_FILE, dtype={'Mosque_ID': str, 'ZCTA': str})

df['ZCTA'] = df['ZCTA'].apply(
    lambda x: str(int(float(x))).zfill(5) if pd.notna(x) else None
)

# Define Census Variables
# B19013_001E = Median Household Income
# B17001_002E = Count of People Below Poverty Level
# B17001_001E = Total Population for whom poverty status is determined
# B25010_001E = Average Household Size
variables = ['NAME', 'B19013_001E', 'B17001_002E', 'B17001_001E', 'B25010_001E']

print("Fetching Census Data (ACS 5-Year)")
census_data = c.acs5.get(variables, geo={'for': 'zip code tabulation area:*'}, year=YEAR)

census_df = pd.DataFrame(census_data)

census_df['Household_Income'] = census_df['B19013_001E']
census_df['Household_Size'] = census_df['B25010_001E']

# Calculate Poverty Rate: (People Below Poverty / Total People) * 100
census_df['Poverty_Rate'] = census_df.apply(
    lambda x: (x['B17001_002E'] / x['B17001_001E'] * 100) if x['B17001_001E'] > 0 else None,
    axis=1
)

census_df['ZCTA'] = census_df['zip code tabulation area']
census_final = census_df[['ZCTA', 'Household_Income', 'Poverty_Rate', 'Household_Size']]
merged_df = pd.merge(df, census_final, on='ZCTA', how='left')

merged_df.to_csv(OUTPUT_FILE, index=False)
print(f"Saved to {OUTPUT_FILE}")
print(merged_df[['ZCTA', 'Household_Income', 'Poverty_Rate', 'Household_Size']].head())