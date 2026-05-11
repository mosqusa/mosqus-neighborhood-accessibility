import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('../data/mosques_scores.csv')

df['Walk_score'] = pd.to_numeric(df['Walk_score'], errors='coerce')
df['Transit_score'] = pd.to_numeric(df['Transit_score'], errors='coerce')

stats = df[['Walk_score', 'Transit_score']].describe().round(2)

print("Descriptive Statistics Table")
print(stats)

missing_walk = df['Walk_score'].isna().sum()
missing_transit = df['Transit_score'].isna().sum()

print("\nMissing Data Counts")
print(f"Mosques missing Walk Score: {missing_walk}")
print(f"Mosques missing Transit Score: {missing_transit}")

plt.figure(figsize=(10, 5))

plt.subplot(1, 2, 1)
df['Walk_score'].hist(bins=20, color='skyblue', edgecolor='black')
plt.title('Distribution of Walk Scores')
plt.xlabel('Score (0-100)')
plt.ylabel('Number of Mosques')

plt.subplot(1, 2, 2)
df['Transit_score'].hist(bins=20, color='salmon', edgecolor='black')
plt.title('Distribution of Transit Scores')
plt.xlabel('Score (0-100)')

plt.tight_layout()
plt.savefig('../data/distribution_plots.png')
print("\nGraphs saved as 'distribution_plots.png'")