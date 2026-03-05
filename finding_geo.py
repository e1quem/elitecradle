from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import requests
import time

def get_geo_data(pob):
    # Cleaning empty values
    if pd.isna(pob) or str(pob).strip() in ["", "foreign", "N/A", "None"]:
        return None
    
    base_url = "https://api-adresse.data.gouv.fr/search/"
    params = {'q': str(pob), 'limit': 1}
    
    try:
        response = requests.get(base_url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['features']:
                best_result = data['features'][0]
                properties = best_result['properties']
                geom = best_result['geometry']['coordinates']
                
                context = properties.get('context', '')
                parts = [p.strip() for p in context.split(',')]
                            
                return {
                    "lon": geom[0],
                    "lat": geom[1],
                    "dept_num": parts[0] if len(parts) > 0 else None,
                    "dep_name": parts[1] if len(parts) > 1 else None,
                    "region": parts[-1] if len(parts) > 2 else None,
                    "confidence": round(properties.get('score', 0), 3)
                }
    except Exception:
        pass
    return None

def process_row(index, row):
    if pd.isna(row['lat']) or str(row['lat']).strip() == "":
        geo = get_geo_data(row['pob'])
        return index, geo
    return index, None


def main():
    # Paths

    # 1. Paths used to find missing geo data of dp.csv
    #input_path = "/Users/eyquem/Desktop/LeadersMap/sources/dp_geo_missing.csv"
    # output_path = "/Users/eyquem/Desktop/LeadersMap/outputs/dp_geo_enriched.csv"

    # 2. Paths used to find the missing geo data of obsolete city name from depute_data.csv (dep_num empty)
    #input_path = "/Users/eyquem/Desktop/LeadersMap/sources/dp_geo_missing_2.csv"
    #output_path = "/Users/eyquem/Desktop/LeadersMap/outputs/dp_geo_enriched_2.csv"

    # 3. Paths used to populate the geo data of senat_data_raw.csv
    #input_path = "/Users/eyquem/Desktop/LeadersMap/outputs/senat_geo_missing.csv"
    #output_path = "/Users/eyquem/Desktop/LeadersMap/outputs/senat_geo_enriched.csv"

    # 4. Paths used for the list of correct pob with foreing dept
    input_path = "/Users/eyquem/Desktop/LeadersMap/sources/senat_foreign_missing.csv"
    output_path = "/Users/eyquem/Desktop/LeadersMap/outputs/senat_foreign_enriched.csv"

    df = pd.read_csv(input_path, sep=None, engine='python')

    cols_to_fix = ['dept_num', 'dept_ob', 'region', 'lat', 'lon', 'confidence']
    for col in cols_to_fix:
        if col not in df.columns:
            df[col] = None
        df[col] = df[col].astype(object)

    total = len(df)
    print(f"Processing {total} entries with missing geo data")

    # Using ThreadPoolExecutor for multithreading
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_row, index, row) for index, row in df.iterrows()]

        for future in as_completed(futures):
            index, geo = future.result()
            if geo:
                df.at[index, 'lon'] = geo['lon']
                df.at[index, 'lat'] = geo['lat']
                df.at[index, 'dept_num'] = geo['dept_num']
                df.at[index, 'dept_ob'] = geo['dep_name']
                df.at[index, 'region'] = geo['region']
                df.at[index, 'confidence'] = geo['confidence']
            else:
                df.at[index, 'dept_ob'] = "foreign"
                df.at[index, 'dept_num'] = "foreign"
                df.at[index, 'region'] = "foreign"
                df.at[index, 'lat'] = None
                df.at[index, 'lon'] = None

            print(f"\r\033[K[{index+1}/{total}]...", end="", flush=True)

    df.to_csv(output_path, index=False, encoding='utf-8')
    print(f"\nDone. Exported results to {output_path}")

if __name__ == "__main__":
    main()