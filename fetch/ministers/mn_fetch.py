from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
from bs4 import BeautifulSoup
import utils as utils
import pandas as pd
import unicodedata
import requests
import socket
import re

# Network config
utils.force_ipv4()

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

keywords = ["minister", "politique", "gouvernement", "femme politique", "homme politique"]
suffixes = ["", "_(homme_politique)", "_(femme_politique)", "_(PDG)", "_(dirigeant)", "_(personnalité_publique)"]

def process(index, name, dob):
    try:
        soup = utils.get_wikipedia_soup(name, headers, suffixes, keywords)
        if soup:
            pob = utils.extract_pob(soup)
            dob = utils.extract_dob(soup)
            return index, pob, dob
        return index, "Not found", "Not found"
    except Exception as e:
        return index, f"Error: {str(e)}", "error"

# Main
if __name__ == "__main__":
    import pandas as pd
    from concurrent.futures import ThreadPoolExecutor

    # Load data
    input_file = "/Users/eyquem/Desktop/LeadersMap/fetch/ministers/src/ministers_list.csv"
    df_raw = pd.read_csv(input_file, sep=None, engine='python')
    
    df = pd.DataFrame(columns=["name", "tag", "dob", "pob"])
    
    for idx in range(len(df_raw)):
            name = str(df_raw.iloc[idx, 1]) + " " + str(df_raw.iloc[idx, 0])
            df = pd.concat([df, pd.DataFrame([{
                "name": name,
                "tag": "minister",
                "dob": "",
                "pob": ""
            }])], ignore_index=True)

    print(f"Scraping wikipedia for dob and pob of {len(df)} ministers...")
    total = len(df)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process, i, row['name'], row['dob']) for i, row in df.iterrows()]
        
        for future in futures:
            idx, pob, dob = future.result()
            df.at[idx, 'pob'] = pob
            df.at[idx, 'dob'] = dob
            print(f"\r\033[K[{idx}/{total}] {df.at[idx, 'name']} : {pob}, {dob}", end="", flush=True)

    output_file = "/Users/eyquem/Desktop/LeadersMap/fetch/ministers/interim/geo_missing.csv"
    df.to_csv(output_file, index=False)
    print(df.head())
    print(f"\nResults saved to {output_file}")