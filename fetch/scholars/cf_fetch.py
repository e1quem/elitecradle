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

base_path = Path("~/EliteCradle").expanduser()

# Network config
utils.force_ipv4()

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
FRANCE_CHECK_CACHE = {}

keywords = ["recherche", "chercheuse", "chercheur", "intellectuel", "professeur", "scientifique", "académie", "université", "thèse", "doctorat", "collège de france", "Collège de France", "universitaire", "biologiste", "physicien", "mathématicien", "chimiste", "sociologue", "historien", "économiste"]
suffixes = ["", "_(universitaire)", "_(scientifique)", "_(chercheur)", "_(professeur)", "_(personnalité_publique)"]


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
    input_file = base_path / "fetch/scholars/src/college_de_france_liste_historique_chaires.xlsx"
    df_raw = pd.read_excel(input_file)
    
    df = pd.DataFrame(columns=["name", "tag", "dob", "pob"])
    
    for idx in range(399, len(df_raw)):
        years = str(df_raw.iloc[idx, 3])
        if "-" in years:
            start, end = years.split("-", 1)
            end = end.strip()
            # We keep only if the course was ongoing during the Fifth Republic, or is still ongoing
            if not end.isdigit() or int(end) >= 1958:
                name = str(df_raw.iloc[idx, 1]) + " " + str(df_raw.iloc[idx, 0])
                df = pd.concat([df, pd.DataFrame([{
                    "name": name,
                    "tag": "college_de_france",
                    "dob": "",
                    "pob": ""
                }])], ignore_index=True)

    print(f"Scraping wikipedia for dob of {len(df)} professors...")
    total = len(df)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process, i, row['name'], row['dob']) for i, row in df.iterrows()]
        
        for future in futures:
            idx, pob, dob = future.result()
            df.at[idx, 'pob'] = pob
            df.at[idx, 'dob'] = dob
            print(f"\r\033[K[{idx}/{total}] {df.at[idx, 'name']} : {pob}, {dob}", end="", flush=True)

    output_file = base_path / "fetch/scholars/interim/cf_geo_missing.csv"
    df.to_csv(output_file, index=False)
    print(df.head())
    print(f"\nResults saved to {output_file}")