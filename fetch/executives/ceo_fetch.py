from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from pathlib import Path
import utils as utils
import pandas as pd
import requests

# Network config
utils.force_ipv4()
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
DOMAIN = "https://fr.wikipedia.org"
base_path = Path("~/elitecradle").expanduser()

def get_category_links(start_url):
    persons = []
    current_url = start_url
    page_count = 1
    
    while current_url:
        print(f"\rObtaining page {page_count}...", end="", flush=True)
        resp = requests.get(current_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        # Extracting links
        groups = soup.find_all("div", class_="mw-category-group")
        for group in groups:
            for link in group.find_all("a", href=True):
                persons.append({
                    "name": link.get("title"),
                    "url": DOMAIN + link["href"],
                    #"tag": "executiveBIS"
                    #"tag": "executiveTER"
                    "tag": "scholar"
                })
                
        # Next page
        next_page = soup.find("a", string="page suivante")
        if next_page:
            current_url = DOMAIN + next_page["href"]
            page_count += 1
        else:
            current_url = None
            
    print(f"\n{len(persons)} individuals.")
    return persons

def process_person(person):
    try:
        resp = requests.get(person["url"], headers=HEADERS, timeout=5)
        if resp.status_code != 200:
            return person
            
        soup = BeautifulSoup(resp.content, 'html.parser')
        raw_pob = utils.extract_pob(soup)
        person["dob"] = utils.extract_dob(soup)
        person["pob_raw"] = raw_pob 
        
        if raw_pob and raw_pob not in ["Unknown", "foreign", "Not found"]:
            geo_data = utils.finding_geo(raw_pob)
            if geo_data:
                geo_data.pop('pop', None)
                person.update(geo_data) 
    except Exception:
        pass
        
    return person

if __name__ == "__main__":
    #category_url = "https://fr.wikipedia.org/wiki/Cat%C3%A9gorie:Chef_d%27entreprise_fran%C3%A7ais"
    #category_url = "https://fr.wikipedia.org/wiki/Cat%C3%A9gorie:Personnalit%C3%A9_fran%C3%A7aise_du_monde_des_affaires_du_XXIe_si%C3%A8cle"
    category_url = "https://fr.wikipedia.org/wiki/Cat%C3%A9gorie:Universitaire_fran%C3%A7ais_du_XXe_si%C3%A8cle"

    persons_list = get_category_links(category_url)
    print("\nScraping profiles and Geo API calls...")
    total = len(persons_list)
    results = []
    
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(process_person, p): p for p in persons_list}
        
        for i, future in enumerate(as_completed(futures), 1):
            res = future.result()
            results.append(res)
            print(f"\r\033[K[{i}/{len(persons_list)}] {res.get('name')} : {res.get('pob_raw')}", end="", flush=True)

    df = pd.DataFrame(results)
    to_drop = ['pob', 'error']
    df = df.drop(columns=[c for c in to_drop if c in df.columns], errors='ignore')

    if 'pob_raw' in df.columns:
        df = df.rename(columns={'pob_raw': 'pob'})

    cols_order = ['name', 'tag', 'dob', 'pob', 'lat', 'lon', 'dep_num', 'dep_name', 'region']
    final_cols = [c for c in cols_order if c in df.columns] + [c for c in df.columns if c not in cols_order]
    df = df[final_cols]
    
    #output_file = base_path / "fetch/executives/interim/CEOs.csv"
    #output_file = base_path / "fetch/executives/interim/business_person.csv"
    output_file = base_path / "fetch/scholars/interim/scholars_raw.csv"

    df.to_csv(output_file, index=False)
    print(f"\nOver: {output_file}")
    print(df.head())