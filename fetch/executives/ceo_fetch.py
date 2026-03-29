from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import pandas as pd
import requests
import utils as utils

# Network config
utils.force_ipv4()
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
DOMAIN = "https://fr.wikipedia.org"

# Source : https://fr.wikipedia.org/w/index.php?title=Catégorie:Chef_d%27entreprise_français&pagefrom=Niel%2C+Xavier%0AXavier+Niel#mw-pages
# Ça ne marche pas quand c'est genre 7ème arrondissement de Paris.

def get_category_links(start_url):
    print("Obtaining links...")
    persons = []
    current_url = start_url
    page_count = 1
    
    while current_url:
        print(f"\rPage {page_count}...", end="", flush=True)
        resp = requests.get(current_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(resp.content, 'html.parser')
        
        # Extracting links
        groups = soup.find_all("div", class_="mw-category-group")
        for group in groups:
            for link in group.find_all("a", href=True):
                persons.append({
                    "name": link.get("title"),
                    "url": DOMAIN + link["href"],
                    "tag": "ceo"
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
        pob = utils.extract_pob(soup)
        person["dob"] = utils.extract_dob(soup)
        person["pob_raw"] = pob 
        
        if pob and pob not in ["Unknown", "foreign", "Not found"]:
            geo_data = utils.finding_geo(pob)
            if geo_data:
                person.update(geo_data) 
            else:
                person["pob"] = pob
        else:
            person["pob"] = pob

    except Exception as e:
        person["error"] = str(e)
        
    return person

if __name__ == "__main__":
    category_url = "https://fr.wikipedia.org/wiki/Cat%C3%A9gorie:Chef_d%27entreprise_fran%C3%A7ais"

    persons_list = get_category_links(category_url)
    print("\nScraping profiles and Geo API calls...")
    total = len(persons_list)
    results = []
    
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {executor.submit(process_person, p): p for p in persons_list}
        
        count = 0
        for future in as_completed(futures):
            count += 1
            result = future.result()
            results.append(result)
            
            name = result.get("name", "Unknown")
            pob = result.get("pob", "N/A")
            print(f"\r\033[K[{count}/{total}] {name} : {pob}", end="", flush=True)

    df = pd.DataFrame(results)
    cols_order = ['name', 'tag', 'dob', 'pob_raw', 'lat', 'lon', 'dep_num', 'dep_name', 'region']
    final_cols = [c for c in cols_order if c in df.columns] + [c for c in df.columns if c not in cols_order]
    df = df[final_cols]
    
    output_file = "/Users/eyquem/Desktop/LeadersMap/fetch/executives/interim/CEOs.csv"
    
    df.to_csv(output_file, index=False)
    print(f"\n\nOpération terminée ! Données sauvegardées dans {output_file}")
    print(df.head())