import utils as utils
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import pandas as pd
import requests
import time
import re

# Solving connection issues for wikipedia
utils.force_ipv4()
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def get_parliament_data_by_id(id):
    # Using parliamentes ids to find their bio on the AN website and extract their pob/dob
    url = f"https://www2.assemblee-nationale.fr/sycomore/fiche/{id}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Name (H1)
        name = " ".join(soup.find("h1").get_text().split()) if soup.find("h1") else "N/A"

        dob = "N/A"
        pob = "N/A"
        dept_ob = "N/A"
        geo_info = None
        info_block = soup.find("dl", class_="sycomore-infos-generales")
        
        if info_block:
            # <li> containing "Né le" or "Née le"
            items = info_block.find_all("li")
            for item in items:
                text = item.get_text().strip()
                if "Né le" in text or "Née le" in text:
                    # Searching the year (4 digits)
                    year_match = re.search(r'\d{4}', text)
                    dob = year_match.group(0) if year_match else "N/A"
                    
                    # Searching the pob (pattern between à and the closing parenthesis). The parenthesis either contains (Department_name - France) or (Country_name)
                    pob_match = re.search(r' à (.*?) \((.*?)\)', text)
                    if pob_match:
                        city_name = pob_match.group(1).strip()
                        bracket_content = pob_match.group(2)

                        if "France" in bracket_content:
                            # We extract the city name and the department name (before " - France")
                            pob = city_name
                            dept_ob = bracket_content.split(" - France")[0].strip()
                            geo_info = utils.finding_geo(pob)
                        else:
                            # France not mentioned : considered foreign
                            # Note : this excludes old colonies, and eventually DOM-TOMs depending on how the AN's website present these cities.
                            pob, dept_ob = "foreign", "foreign"
                    else:
                        pob, dept_ob = "foreign", "foreign"
                    break

        return {
            "name": name,
            "tag": "parliament",
            "dob": dob,
            "pob": geo_info["pob"] if geo_info else pob,
            "dept_num": geo_info["dep_num"] if geo_info else ("foreign" if pob == "foreign" else None),
            "dept_ob": geo_info["dep_name"] if geo_info else ("foreign" if pob == "foreign" else None),
            "region": geo_info["region"] if geo_info else ("foreign" if pob == "foreign" else None),
            "lat": geo_info["lat"] if geo_info else None,
            "lon": geo_info["lon"] if geo_info else None,
            "confidence" : geo_info["confidence"] if geo_info else None, 
            "id": id
        }

    except Exception as e:
        print(f"Error on {id}: {e}")
        return None
    
# 1. Obtaining the list of all departments
# Use list of departments extracted from https://www2.assemblee-nationale.fr/sycomore/recherche
with open("/Users/eyquem/Desktop/EliteGeoCradle/fetch/parliament/src/departments_raw.txt", "r", encoding="utf-8") as f:
    content = f.read()
soup = BeautifulSoup(content, 'html.parser') 

# Removing departments that have only one historical parliamentes: the page has a different format.
wrong_format = [
    "Côte-d'Ivoire", 
    "Gabon", 
    "Gabon-Moyen-Congo", 
    "Mauritanie", 
    "Moyen-Congo", 
    "Oubangui-Chari", 
    "Oubangui-Chari-Tchad"
]

# We manually keep the info of these parliamentes.
manual_data = [
    {"name": "Félix Houphouët-Boigny", "dept": "Côte-d'Ivoire", "id": "3874", "pob": "foreign", "dept_ob": "foreign"},
    {"name": "Jean-Hilaire Aubame", "dept": "Gabon", "id": "226", "pob": "foreign", "dept_ob": "foreign"},
    {"name": "Maurice Albert Henri Bayrou", "dept": "Gabon-Moyen-Congo", "id": "517", "pob": "Lanta", "dept_ob": "Haute-Garonne"},
    {"name": "N'Diaye Sidi El Moktar", "dept": "Mauritanie", "id": "6830", "pob": "foreign", "dept_ob": "foreign"},
    {"name": "Jean Félix-Tchicaya", "dept": "Moyen-Congo", "id": "2955", "pob": "foreign", "dept_ob": "foreign"},
    {"name": "Barthélémy Boganda", "dept": "Oubangui-Chari", "id": "893", "pob": "foreign", "dept_ob": "foreign"},
    {"name": "René Malbrant", "dept": "Oubangui-Chari-Tchad", "id": "4923", "pob": "Dangé", "dept_ob": "Vienne"}
]
df_manual = pd.DataFrame(manual_data)

# Cleaning and sorting departments
departments = sorted(list(set([li.get_text().strip() for li in soup.find_all('li') if li.get_text().strip() not in wrong_format])))
print(f"{len(departments)} departments extracted")

# 2. We need this list of departments because pagination is broken on the AN website. It doesn't properly display the right names after the 500 pagination limit.
# Hence we cannot do a simple search for all parliamentes since the beginning of the Vth Républic
# Instead, we do one request for each departement in order to stay under the 500 results limit (even Paris only has 226 results)
base_url = "https://www2.assemblee-nationale.fr/sycomore/resultats/"
query_params = "?base=tous_departements&regle_nom=est&nom=&departement={dep_encoded}&choixdate=intervalle&debutmin=09/12/1958&finmin=&dateau=&legislature=&choixordre=chrono&submitbas=Lancer+la+recherche"
all_dp = []
total_depts = len(departments)

for i, dept in enumerate(departments, 1):
    print(f"\r\033[K[{i}/{total_depts}] Obtaining list of parliamentes for {dept}...", end="", flush=True)

    dep_encoded = quote_plus(dept)
    url = f"{base_url}{query_params.format(dep_encoded=dep_encoded)}"
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Error {response.status_code} on {dept}")
            continue
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Identify web page content
        table = soup.find("table", {"class": "sycomore"})
        if not table:
            break
        rows = table.find_all("tr")[1:]
        
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2:
                link_tag = cells[0].find("a")

                # Extracting the name and the fiche id from the link
                if link_tag:
                    name = link_tag.get_text().strip()
                    relative_url = link_tag.get("href")
                    id = re.search(r'\d+', relative_url).group(0)
  
                all_dp.append({
                    "id": id,
                    "name": name,
                    "dept": dept
                })
    
        time.sleep(0.1)

    except Exception as e:
        print(f"Error on {dept} : {e}")

df = pd.DataFrame(all_dp)

# Cleaning
# We add the correct pob for André Godin, the AN website indicated "625274982"
df.loc[df['name'] == 'André Godin', 'pob'] = 'Bourg-en-Bresse'
# We consider an entry is a duplicate if the name and the id are identical
df = df.drop_duplicates(subset=['name', 'id'], keep='first')

print(f"\nFound {len(df)+7} parliamentes.")
new_results = []
total_dp = len(df)

# 3. Obtaining full geo info using their individual id and data.gouv API
for index, row in df.iterrows():
    id = str(row['id'])
    data = get_parliament_data_by_id(id)
    if data:
        print(f"\r\033[K[{index+1}/{total_dp}] {data['name']}...", end="", flush=True)
        new_results.append(data)
    else:
        print(f"\r\033[K[{index+1}/{total_dp}] ID {id} : Error fetching data.", end="", flush=True)
df_details = pd.DataFrame(new_results)
manual_results = []

# 3.bis Obtaining full geo info of manually extracted parliamentes
for index, row in df_manual.iterrows():
    name, id, pob, dept_ob, dob = row['name'], row['id'], row['pob'], row['dept_ob'], "N/A"
    geo_info = utils.finding_geo(pob)

    manual_results.append({
            "name": name,
            "tag": "parliament",
            "dob": dob,
            "pob": pob,
            "dept_num": geo_info["dep_num"] if geo_info else ("foreign" if pob == "foreign" else None),
            "dept_ob": geo_info["dep_name"] if geo_info else ("foreign" if pob == "foreign" else None),
            "region": geo_info["region"] if geo_info else ("foreign" if pob == "foreign" else None),
            "lat": geo_info["lat"] if geo_info else None,
            "lon": geo_info["lon"] if geo_info else None,
            "confidence" : geo_info["confidence"] if geo_info else None, 
            "id": id
        })
    
df_manual = pd.DataFrame(manual_results)
df = pd.concat([df_details, df_manual], ignore_index=True)

# 4. Obtaining precise arrondissement for parisian parliamentes
# Filtering parisian parliamentes
df_paris = df[
    (df['dept_num'] == '75') |
    (df['pob'].str.contains(r'Paris', case=False, na=False))
].copy()
total = len(df_paris)

# Finding the arrondissement using wikipedia
suffixes = ["", "_(homme_politique)", "_(femme_politique)", "_(personnalité_politique)"]
keywords = ["politique", "député", "députée", "assemblée nationale", "circonscription"]

for index, row in df_paris.iterrows():
    name, year = row['name'], row['dob']
    print(f"\n[{index+1}/{total}] Verifying : {name}...", end="", flush=True)

    try:
        # Finding the page with name variations
        soup, final_url = utils.get_wikipedia_soup(name, headers, suffixes=suffixes, keywords=keywords)
        if soup:
            pob_final = utils.extract_arrondissement(soup)
            df_paris.at[index, 'pob'] = pob_final
        else:
            df_paris.at[index, 'pob'] = "Paris"
                
    except Exception as e:
        df_paris.at[index, 'pob'] = "Paris"
    
df_paris_standardized = utils.standardize_arrondissements(df_paris)
count = len(df[df['pob'].str.contains(r'Paris \d', na=False)])
print(f"\nFound {count} arr. out of {total} entries ({round(count/total*100, 2)}%)")

# Fusionning Parisian arrondissements
df = pd.update([df, df_paris_standardized], ignore_index=True)

# Saving as CSV
output_path = "/Users/eyquem/Desktop/EliteGeoCradle/fetch/parliament/interim/dp_geo_enrich.csv"
df.to_csv(output_path, index=False, encoding='utf-8')