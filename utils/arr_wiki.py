from urllib.parse import quote
from bs4 import BeautifulSoup
import pandas as pd
import unicodedata
import requests
import socket
import time
import re


# Config for connection issues
def force_ipv4():
    old_getaddrinfo = socket.getaddrinfo
    def new_getaddrinfo(*args, **kwargs):
        responses = old_getaddrinfo(*args, **kwargs)
        return [r for r in responses if r[0] == socket.AF_INET]
    socket.getaddrinfo = new_getaddrinfo
force_ipv4()


def is_correct_profile(soup, target_name, target_year):
    page_text = soup.get_text().lower()
    h1 = soup.find("h1", {"id": "firstHeading"})
    h1_text = h1.get_text().lower() if h1 else ""
    
    # An "homonymie" wikipedia page is directly rejected
    cats = soup.find("div", {"id": "mw-normal-catlinks"})
    cats_text = cats.get_text().lower() if cats else ""
    if "homonymie" in cats_text or "homonymie" in h1_text:
        return False

    clean_target = target_name.lower().replace(',', '')
    name_parts = clean_target.split()

    # 1. Name partially matches H1 title
    name_match = any(part in h1_text for part in name_parts)

    # 2. Keywords are found in the page
    is_politician = any(kw in page_text for kw in ["politique", "député", "députée" "assemblée nationale", "circonscription"])

    # 3. Checking dob year to avoid hononyms
    has_year = str(target_year) in page_text if (target_year and str(target_year) != "nan") else True
    
    print(f" | Name match: {name_match}, Is politician: {is_politician}, Year match: {has_year}", end="")
    
    return name_match and is_politician and has_year


def get_wikipedia_soup(name, year, headers):
    # Finding URL variations to obtain the correct page
    # Cleaning: "Pierre, Guy Coulon" becomes "Pierre_Guy_Coulon"
    clean_name = name.replace(',', '').strip()
    base_formatted = clean_name.replace(' ', '_')
    
    # For homonyms, wikipedia adds a parenthesis with a descriptor. We try the most common ones.
    variations = [
        base_formatted,
        f"{base_formatted}_(homme_politique)",
        f"{base_formatted}_(femme_politique)"
        f"{base_formatted}_(personnalité_politique)",
    ]
    
    # Special case : "Name1, Name2 Name3" -> "Name1 Name3" (ex: Pierre Guy Coulon page is under "Pierre_Coulon")
    parts = clean_name.split()
    if len(parts) > 2:
        short_name = f"{parts[0]}_{parts[-1]}"
        variations.append(short_name)
        variations.append(f"{short_name}_(homme_politique)")

    for variant in variations:
        url = f"https://fr.wikipedia.org/wiki/{quote(variant)}"
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, 'html.parser')

                # We check if the page is correct
                if is_correct_profile(soup, name, year):
                    print(f" | Found with : {variant}", end="", flush=True)
                    return soup, url

        except Exception:
            continue

    print(" | No valid page found", end="", flush=True)        
    return None, None


def extract_paris_arrondissement(soup):
    # Dictionnary of roman numerals
    roman_map = {
        'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
        'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15, 'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19, 'XX': 20
    }

    def clean_txt(text):
        return unicodedata.normalize("NFKD", text).lower().strip()

    # 1. Searching throughout the categories
    cats_div = soup.find("div", {"id": "mw-normal-catlinks"})
    if cats_div:
        for link in cats_div.find_all("a", href=True):
            href = link["href"]
            if "arrondissement_de_Paris" in href:
                m = re.search(r"(\d{1,2})(?:er|e)_arrondissement", href)
                if m:
                    val = int(m.group(1))
                    print(f" | Paris {val}", end="", flush=True)
                    return f"Paris {val}"

    # 2. "Lieu de naissance" (pob) in infobox
    infobox = soup.find("table", {"class": "infobox"})
    if infobox:
        for row in infobox.find_all("tr"):
            row_text = row.get_text().lower()
            if "naissance" in row_text and "paris" in row_text:
                m_arab = re.search(r"paris.*?(\d{1,2})|(\d{1,2})\s*(?:er|e|eme|ème)\s*arrondissement", row_text)
                if m_arab:
                    val = m_arab.group(1) or m_arab.group(2)
                    if val:
                        print(f" | Paris {int(val)}", end="", flush=True)
                        return f"Paris {int(val)}"
                    
                m_rom = re.search(r"paris\s+([ivxl]+)", row_text)
                if m_rom:
                    val_rom = m_rom.group(1).upper()
                    if val_rom in roman_map:
                        print(f" | Paris {roman_map[val_rom]}", end="", flush=True)
                        return f"Paris {roman_map[val_rom]}"

    # 3. Introductory paragraph
    content = soup.find("div", {"class": "mw-parser-output"})
    if content:
        p = content.find("p", recursive=False)
        if p:
            txt = clean_txt(p.get_text())
            m = re.search(r"paris\s+(?:0?(\d{1,2}))|(\d{1,2})\s*(?:er|e|eme|ème)\s*arrondissement", txt)
            if m:
                val = m.group(1) or m.group(2)
                print(f" | Paris {int(val)}", end="", flush=True)
                return f"Paris {int(val)}"
            
            m_rom = re.search(r"paris\s+([ivxl]+)", txt)
            if m_rom:
                val_rom = m_rom.group(1).upper()
                if val_rom in roman_map:
                    print(f" | Paris {roman_map[val_rom]}", end="", flush=True)
                    return f"Paris {roman_map[val_rom]}"

    print(" | No arr. found.", end="", flush=True)
    return "Paris"


# Paths for dp
input_path = "/Users/eyquem/Desktop/LeadersMap/sources/dp_arr_missing.csv"
output_path = "/Users/eyquem/Desktop/LeadersMap/outputs/dp_arr_enriched.csv"

df = pd.read_csv(input_path, sep=None, engine='python')
total = len(df)
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

for index, row in df.iterrows():
    name = row['name']
    year = row['dob']
    print(f"\n[{index+1}/{total}] Verifying : {name}...", end="", flush=True)

    try:
        # Finding the page with the name variations
        soup, final_url = get_wikipedia_soup(name, year, headers)
        
        if soup:
            pob_final = extract_paris_arrondissement(soup)
            df.at[index, 'pob'] = pob_final
        else:
            df.at[index, 'pob'] = "Paris"
                
    except Exception as e:
        df.at[index, 'pob'] = "Paris"
    

count = len(df[df['pob'].str.contains(r'Paris \d', na=False)])
print(f"\nFound {count} arr. out of {total} entries ({round(count/total*100, 2)}%)")

# Save
df.to_csv(output_path, index=False)
print(f"File: {output_path}")