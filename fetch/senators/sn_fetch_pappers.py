from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
from bs4 import BeautifulSoup
from pathlib import Path
import utils as utils
import pandas as pd
import unicodedata
import requests
import socket
import re

base_path = Path("~/elitecradle").expanduser()

# Network config
utils.force_ipv4()

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
FRANCE_CHECK_CACHE = {}

keywords = ["politique", "sénat", "sénateur", "maire", "parlementaire"]
suffixes = ["", "_(homme_politique)", "_(femme_politique)", "_(personnalité_publique)"]

def process(index, name, dob):
    try:
        soup = utils.get_wikipedia_soup(name, headers, suffixes, keywords)
        if soup:
            pob = utils.extract_pob(soup)
            return index, pob
        return index, "Not found"
    except Exception as e:
        return index, f"Error: {str(e)}"

# Main
if __name__ == "__main__":
    # Load data and creating df
    input_file = base_path / "fetch/senators/src/data.senat_Informations_generales_sur_les_senateurs.xls"
    df_raw = pd.read_excel(input_file)
    
    df = pd.DataFrame()
    df["name"] = df_raw.iloc[:, 3] + " " + df_raw.iloc[:, 2]  
    df["tag"] = "senat"
    df["dob"] = pd.to_datetime(df_raw.iloc[:, 5], errors='coerce').dt.year
    df["pob"] = ""

    print(f"Scraping wikipedia for dob of {len(df)} senators...")
    total = len(df)

    with ThreadPoolExecutor(max_workers=10) as executor: # Using 10 threads
        futures = [executor.submit(process, i, row['name'], row['dob']) for i, row in df.iterrows()]
        
        for future in futures:
            idx, res = future.result()
            df.at[idx, 'pob'] = res
            print(f"\r\033[K[{idx+1}/{total}] {df.at[idx, 'name']} : {res}", end="", flush=True)

    output_file = base_path / "fetch/senators/interim/sn_geo_missing.csv"
    df.to_csv(output_file, index=False)
    print(df.head())
    print(f"\nResults saved to {output_file}")