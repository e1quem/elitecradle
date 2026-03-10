import pandas as pd

# Path
#path = "/Users/eyquem/Desktop/LeadersMap/outputs/sn_geo_enriched.csv"
#path = "/Users/eyquem/Desktop/LeadersMap/outputs/cf_geo_enriched.csv"
path = "/Users/eyquem/Desktop/LeadersMap/outputs/mn_geo_enriched.csv"
df = pd.read_csv(path, sep=None, engine='python')

# Precise coordinates
paris_arrondissements = {
    "Paris 1": (48.863826751708984, 2.3342583179473877),
    "Paris 3": (48.863365173339844, 2.358234405517578),
    "Paris 4": (48.854515075683594, 2.3588101863861084),
    "Paris 5": (48.8465576171875, 2.3515963554382324),
    "Paris 6": (48.85261154174805, 2.3332111835479736),
    "Paris 7": (48.857215881347656, 2.3098840713500977),
    "Paris 8": (48.87311553955078, 2.310023307800293),
    "Paris 9": (48.872615814208984, 2.340359926223755),
    "Paris 10": (48.87582778930664, 2.360285758972168),
    "Paris 11": (48.86030960083008, 2.3786137104034424),
    "Paris 12": (48.836666107177734, 2.403441905975342),
    "Paris 13": (48.836666107177734, 2.403441905975342),
    "Paris 14": (48.83161926269531, 2.3244473934173584),
    "Paris 15": (48.84374237060547, 2.2927637100219727),
    "Paris 16": (48.86101150512695, 2.2834136486053467),
    "Paris 17": (48.88784408569336, 2.3070974349975586),
    "Paris 18": (48.8870221, 2.3478318),
    "Paris 19": (48.88661575317383, 2.384809970855713),
    "Paris 20": (48.863311767578125, 2.3996946811676025),
}

# Updating lon et lat
for index, row in df.iterrows():
    pob = row['pob']
    if pob in paris_arrondissements:
        lat, lon = paris_arrondissements[pob]
        df.at[index, 'lat'] = lat
        df.at[index, 'lon'] = lon

# Save
df.to_csv(path, index=False, encoding='utf-8')

print(f"Done. {path}.")