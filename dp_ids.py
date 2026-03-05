from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import pandas as pd
import requests
import time
import re

# 1. Extracting the list of all departments

# Opening the list of departments extracted from https://www2.assemblee-nationale.fr/sycomore/recherche
with open("/Users/eyquem/Desktop/LeadersMap/sources/departments_raw.txt", "r", encoding="utf-8") as f:
    content = f.read()

# Extracting the names
soup = BeautifulSoup(content, 'html.parser') 

# Removing these departments: thay have only one historical deputees and have a different format.
wrong_format = [
    "Côte-d'Ivoire", 
    "Gabon", 
    "Gabon-Moyen-Congo", 
    "Mauritanie", 
    "Moyen-Congo", 
    "Oubangui-Chari", 
    "Oubangui-Chari-Tchad"
]

# We manually kept the name of these deputees in a different df.
manual_data = [
    {"name": "Félix Houphouët-Boigny", "dept": "Côte-d'Ivoire", "id": "3874"},
    {"name": "Jean-Hilaire Aubame", "dept": "Gabon", "id": "226"},
    {"name": "Maurice Albert Henri Bayrou", "dept": "Gabon-Moyen-Congo", "id": "517"},
    {"name": "N'Diaye Sidi El Moktar", "dept": "Mauritanie", "id": "6830"},
    {"name": "Jean Félix-Tchicaya", "dept": "Moyen-Congo", "id": "2955"},
    {"name": "Barthélémy Boganda", "dept": "Oubangui-Chari", "id": "893"},
    {"name": "René Malbrant", "dept": "Oubangui-Chari-Tchad", "id": "4923"}
]
df_manual = pd.DataFrame(manual_data)

# Cleaning and sorting departments
departments = sorted(list(set([li.get_text().strip() for li in soup.find_all('li') if li.get_text().strip() not in wrong_format])))
print(f"{len(departments)} departments extracted")

# 2. Using this list to obtain the full list of deputees per department during the Fifth Republic

# Configuration of the research url
# Pagination is broken on the website. Instead, we loop through departments in order to stay under the 500 results per request limit.
base_url = "https://www2.assemblee-nationale.fr/sycomore/resultats/"
query_params = "?base=tous_departements&regle_nom=est&nom=&departement={dep_encoded}&choixdate=intervalle&debutmin=09/12/1958&finmin=&dateau=&legislature=&choixordre=chrono&submitbas=Lancer+la+recherche"
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

all_dp = []
total_depts = len(departments)

for i, dept in enumerate(departments, 1):

    # Progress indicator
    print(f"\r\033[K[{i}/{total_depts}] {dept}...", end="", flush=True)

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
            
        # Extracting lines of the table
        rows = table.find_all("tr")[1:]
        
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 2:
                link_tag = cells[0].find("a")

                # Extracting the name and the fiche id from the linkg
                if link_tag:
                    name = link_tag.get_text().strip()
                    relative_url = link_tag.get("href")
                    id = re.search(r'\d+', relative_url).group(0)

                
                all_dp.append({
                    "id": id,
                    "name": name,
                    "dept": dept
                })
        
        # API rate limiting
        time.sleep(0.1)

    except Exception as e:
        print(f"Error on {dept} : {e}")

# Results
df = pd.DataFrame(all_dp)

# We fusion the two dataframes
df = pd.concat([df, df_manual], ignore_index=True)

# We consider an entry is a duplicate if the name and the id are identical
df = df.drop_duplicates(subset=['name', 'id'], keep='first')

print(f"\nFound {len(df)} deputees.")

# Saving as CSV
output_path = "/Users/eyquem/Desktop/LeadersMap/outputs/dp_id.csv"
df.to_csv(output_path, index=False, encoding='utf-8')