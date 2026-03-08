from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
from bs4 import BeautifulSoup
import pandas as pd
import unicodedata
import requests
import socket
import re

# Network config
def force_ipv4():
    old_getaddrinfo = socket.getaddrinfo
    def new_getaddrinfo(*args, **kwargs):
        responses = old_getaddrinfo(*args, **kwargs)
        return [r for r in responses if r[0] == socket.AF_INET]
    socket.getaddrinfo = new_getaddrinfo
force_ipv4()

HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
FRANCE_CHECK_CACHE = {}

def is_in_france(city_url):
    if not city_url or not city_url.startswith("/wiki/"):
        return True # Default to true if no link
    
    if city_url in FRANCE_CHECK_CACHE:
        return FRANCE_CHECK_CACHE[city_url]
    
    try:
        full_url = f"https://fr.wikipedia.org{city_url}"
        resp = requests.get(full_url, headers=HEADERS, timeout=3)
        if resp.status_code == 200:
            content = resp.text.lower()
            # Searching for France keywords
            found = any(word in content for word in ["france", "français", "française"])
            FRANCE_CHECK_CACHE[city_url] = found
            return found
    except:
        pass
    return True

def is_correct_profile(soup, target_name):
    page_text = soup.get_text().lower()
    h1 = soup.find("h1", {"id": "firstHeading"})
    h1_text = h1.get_text().lower() if h1 else ""
    
    # Reject homonymie pages
    cats = soup.find("div", {"id": "mw-normal-catlinks"})
    cats_text = cats.get_text().lower() if cats else ""
    if "homonymie" in cats_text or "homonymie" in h1_text:
        return False

    clean_target = target_name.lower().replace(',', '')
    name_parts = clean_target.split()

    # 1. Check for name match
    name_match = any(part in h1_text for part in name_parts)
    
    # 2. Check for keyword match
    is_politician = any(kw in page_text for kw in ["homme d'affaires", "ingénieur", "femme d'affaires", "actionnaire", "affaire", "administrateur", "entreprise", "gouvernement", "banque", "finance", "directeur", "directrice", "CAC40"])
    
    return name_match and is_politician

def extract_paris_arrondissement(soup):

    roman_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
                 'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19, 'XX': 20}
    
    def clean_txt(text):
        return unicodedata.normalize("NFKD", text).lower().strip()

    # 1. Categories
    cats_div = soup.find("div", {"id": "mw-normal-catlinks"})
    if cats_div:
        for link in cats_div.find_all("a", href=True):
            if "arrondissement_de_Paris" in link["href"]:
                m = re.search(r"(\d{1,2})(?:er|e)_arrondissement", link["href"])
                if m: return f"Paris {int(m.group(1))}"

    # 2. Infobox
    infobox = soup.find("table", {"class": "infobox"})
    if infobox:
        for row in infobox.find_all("tr"):
            row_text = row.get_text().lower()
            if "naissance" in row_text and "paris" in row_text:
                m_arab = re.search(r"paris.*?(\d{1,2})|(\d{1,2})\s*(?:er|e|eme|ème)\s*arrondissement", row_text)
                if m_arab: return f"Paris {int(m_arab.group(1) or m_arab.group(2))}"
                m_rom = re.search(r"paris\s+([ivxl]+)", row_text)
                if m_rom and m_rom.group(1).upper() in roman_map:
                    return f"Paris {roman_map[m_rom.group(1).upper()]}"

    # 3. Intro
    content = soup.find("div", {"class": "mw-parser-output"})
    if content:
        p = content.find("p", recursive=False)
        if p:
            txt = clean_txt(p.get_text())
            m = re.search(r"paris\s+(?:0?(\d{1,2}))|(\d{1,2})\s*(?:er|e|eme|ème)\s*arrondissement", txt)
            if m: return f"Paris {int(m.group(1) or m.group(2))}"
            m_rom = re.search(r"paris\s+([ivxl]+)", txt)
            if m_rom and m_rom.group(1).upper() in roman_map:
                return f"Paris {roman_map[m_rom.group(1).upper()]}"
    
    return "Paris"

def extract_pob(soup):
    infobox = soup.find("table", {"class": "infobox"})
    
    # 1. Infobox
    if infobox:
        for row in infobox.find_all("tr"):

            # Searching for "Lieu de Naissance"
            if "lieu de naissance" in row.get_text().lower():
                td = row.find("td")
                if td:
                    # Paris : arr. logic
                    if "paris" in td.get_text().lower():
                        return extract_paris_arrondissement(soup)
                    # Check if it's french or foreign
                    link = td.find("a", href=True)
                    if link:
                        if not is_in_france(link['href']): return "foreign"
                        city = link.get_text()
                    else:
                        city = td.get_text(separator=" ").split('(')[0].split('[')[0]
                    return city.strip()

    # 2. Categories
    cats = soup.find("div", {"id": "mw-normal-catlinks"})
    if cats:
        # Looking for "Naissance à ..." category
        cat_link = cats.find("a", string=re.compile(r"Naissance à .+"))
        if cat_link:
            cat_text = cat_link.get_text()
            
            # Simple check for Paris in categories
            if "paris" in cat_text.lower():
                return extract_paris_arrondissement(soup)
                
            if not is_in_france(cat_link['href']): 
                return "foreign"
                
            return cat_text.replace("Naissance à ", "").strip()

    # 3. Intro paragraph
    content = soup.find("div", {"class": "mw-parser-output"})
    if content:
        p = content.find("p", recursive=False)
        if p:
            p_text = p.get_text()
            # Regex captures the city name after "à"
            match = re.search(r"n[ée]e?\s+(?:le\s+[^à]{1,30}?\s+)?à\s+([A-Z][\w\s\-]{1,20})", p_text)
            if match:
                city_name = match.group(1).strip()

                # Simple Paris check for the intro
                if "paris" in city_name.lower():
                    return extract_paris_arrondissement(soup)
                link = p.find("a", string=re.compile(re.escape(city_name)))
                if link and not is_in_france(link['href']): 
                    return "foreign"
                
                return city_name

    return "Unknown"

def extract_dob(soup):
    # Infobox "naissance"
    infobox = soup.find("table", {"class": "infobox"})
    if infobox:
        for row in infobox.find_all("tr"):
            if "naissance" in row.get_text().lower():
                time_tag = row.find("time", {"class": "date-lien"})
                if time_tag and "datetime" in time_tag.attrs:
                    return int(time_tag["datetime"].split("-")[0])
                year_link = row.find("a", href=re.compile(r"/wiki/\d{4}"))
                if year_link:
                    return int(year_link.get_text())

    # Introductory paragraph
    content = soup.find("div", {"class": "mw-parser-output"})
    if content:
        p = content.find("p", recursive=False)
        if p:
            match = re.search(r"n[ée]e?\s+(?:le\s+\d{1,2}\s+[^\d]+\s+)?(\d{4})", p.get_text())
            if match:
                return int(match.group(1))

    # Categories
    cats = soup.find("div", {"id": "mw-normal-catlinks"})
    if cats:
        for link in cats.find_all("a"):
            if "naissance" in link.get_text().lower():
                match = re.search(r"(\d{4})", link.get_text())
                if match:
                    return int(match.group(1))

    return None


def get_wikipedia_soup(name):
    # Fetch wikipedia content
    clean_name = name.replace(',', '').strip()
    base_formatted = clean_name.replace(' ', '_')
    variations = [base_formatted, ]
    variations = [base_formatted, f"{base_formatted}_(personalité_publique)", f"{base_formatted}_(chevalier_de_la_Légion_d'honneur)", f"{base_formatted}_(PDG)", f"{base_formatted}_(dirigeant)", f"{base_formatted}_(homme_d'affaire)", f"{base_formatted}_(femme_d'affaire)", f"{base_formatted}_(entrepreneur)"]
    
    for variant in variations:
        url = f"https://fr.wikipedia.org/wiki/{quote(variant)}"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, 'html.parser')
                if is_correct_profile(soup, name):
                    return soup
        except: continue
    return None

def process(index, name, dob):
    try:
        soup = get_wikipedia_soup(name)
        if soup:
            pob = extract_pob(soup)
            dob = extract_dob(soup)
            return index, pob, dob
        return index, "Not found", "Not found"
    except Exception as e:
        return index, f"Error: {str(e)}", "error"

# Main

if __name__ == "__main__":
    import pandas as pd
    from concurrent.futures import ThreadPoolExecutor

    # Load data
    input_file = "/Users/eyquem/Desktop/LeadersMap/outputs/cac_staff.csv"
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

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process, i, row['name'], row['dob']) for i, row in df.iterrows()]
        
        for future in futures:
            idx, pob, dob = future.result()
            df.at[idx, 'pob'] = pob
            df.at[idx, 'dob'] = dob
            print(f"\r\033[K[{idx}/{total}] {df.at[idx, 'name']} : {pob}, {dob}", end="", flush=True)

    output_file = "/Users/eyquem/Desktop/LeadersMap/outputs/cac_geo_missing.csv"
    df.to_csv(output_file, index=False)
    print(df.head())
    print(f"\nResults saved to {output_file}")