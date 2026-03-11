from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
from bs4 import BeautifulSoup
import utils.utils as utils
import pandas as pd
import unicodedata
import requests
import socket
import re

# Network config
utils.force_ipv4()
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

keywords = ["homme d'affaires", "femme d'affaires", "ingénieur", "actionnaire", "administrateur", "entreprise", "gouvernement", "banque", "finance", "directeur", "directrice", "CAC40"]
suffixes = ["", "_(personnalité_publique)", "_(chevalier_de_la_Légion_d'honneur)", "_(PDG)", "_(dirigeant)", "_(homme_d'affaire)", "_(femme_d'affaire)", "_(entrepreneur)"]


def process(index, name, dob):
    try:
        soup, final_url = utils.get_wikipedia_soup(name, headers, suffixes, keywords)
        
        if soup:
            pob = utils.extract_pob(soup)
            dob_extracted = utils.extract_dob(soup)
            geo_data = utils.finding_geo(pob)
            
            return {
                "index": index,
                "pob": pob,
                "dob": dob_extracted or "Unknown",
                "lat": geo_data["lat"] if geo_data else None,
                "lon": geo_data["lon"] if geo_data else None,
                "dep_num": geo_data["dep_num"] if geo_data else None,
                "region": geo_data["region"] if geo_data else None
            }
        return {"index": index, "pob": "Not found", "dob": "Not found"}
    except Exception as e:
        return {"index": index, "pob": f"Error: {str(e)}", "dob": "error"}


# Main
if __name__ == "__main__":
    import pandas as pd
    from concurrent.futures import ThreadPoolExecutor

    # Load data
    input_file = "/Users/eyquem/Desktop/LeadersMap/fetch/executives/interim/execs.csv"
    df_raw = pd.read_csv(input_file, sep=None, engine='python')
    
    df = pd.DataFrame(columns=["name", "tag", "dob", "pob"])
    
    for idx in range(len(df_raw)):
            name = str(df_raw.iloc[idx, 0])
            df = pd.concat([df, pd.DataFrame([{
                "name": name,
                "tag": "executive",
                "dob": "",
                "pob": ""
            }])], ignore_index=True)

    print(f"Scraping wikipedia for dob and pob of {len(df)} executives...")
    total = len(df)

    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = [executor.submit(process, i, row['name'], row['dob']) for i, row in df.iterrows()]
        
        for future in futures:
            result = future.result() # On récupère le dictionnaire complet
            idx = result["index"]
            
            for key in ["pob", "dob", "lat", "lon", "dep_num", "region"]:
                if key in result:
                    if key not in df.columns:
                        df[key] = None
                    df.at[idx, key] = result[key]
            
            print(f"\r\033[K[{idx}/{total}] {df.at[idx, 'name']} : {result.get('pob')}, {result.get('dob')}", end="", flush=True)

    output_file = "/Users/eyquem/Desktop/LeadersMap/fetch/executives/interim/exec_geo_enriched.csv"
    df.to_csv(output_file, index=False)
    print(df.head())
    print(f"\nResults saved to {output_file}")