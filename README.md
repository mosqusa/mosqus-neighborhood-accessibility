# Mosque Neighborhood Accessibility

This project collects walkability, transit, and socioeconomic data for mosques across the US.

---

## What It Does

**Step 1: Scrape Walk and Transit Scores** (`scrape_scores.py`) - Research Question 3
Reads the mosque database, fills in coordinates from each mosque's address, then looks up Walk Score and Transit Score for each location.

**Step 2: Score Statistics** (`scores_stats.py`) - Research Question 3
Reads the scores file and prints a summary table of Walk and Transit scores. Also saves a chart of the score distributions.

**Step 3: Census Data** (`census_data_pull.py`) - Research Question 2b
Reads the scores file and pulls neighborhood socioeconomic data (household income, poverty rate, household size) from the US Census for each mosque's zip code.

---

## Files

```
data/
  CLEAN_USMosqueDatabase(Physical-Spatial).csv   <- starting input file
  mosques_scores.csv                             <- output of Step 1, input for Steps 2 and 3
  mosques_socioeconomic.csv                      <- final output of Step 3
  distribution_plots.png                         <- chart output of Step 2

mosque_accessibility/
  scrape_scores.py                               <- Step 1
  scores_stats.py                                <- Step 2

neighborhood_socioeconomic/
  census_data_pull.py                            <- Step 3
```

---

## Setup

### 1. Install Python packages

```
pip install pandas requests beautifulsoup4 geopy python-dotenv census
```

### 2. Add your Census API key

Create a file called `.env` in the root folder with this line:

```
CENSUS_API_KEY=your_key_here
```

You can get a free Census API key at https://api.census.gov/data/key_signup.html

---

## How to Run

Run the scripts in order. Each one must finish before starting the next.

**Step 1** - from inside the `mosque_accessibility/` folder:
```
python scrape_scores.py
```
This takes a while (~1-2 seconds per mosque). Progress saves automatically every 100 rows, so it is safe to stop and restart.

**Step 2** - from inside the `mosque_accessibility/` folder:
```
python scores_stats.py
```

**Step 3** - from inside the `neighborhood_socioeconomic/` folder:
```
python census_data_pull.py
```

---

## Notes

- Step 1 will skip mosques that already have Walk and Transit scores, so re-running it picks up where it left off.
- If a mosque address cannot be found by the geocoder, its Latitude and Longitude will be blank but its Walk and Transit score may still be collected.
- The Census API uses zip codes (ZCTA) to match neighborhood data, so mosques without a valid ZCTA will have blank socioeconomic columns in the final output.