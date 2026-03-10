from bs4 import BeautifulSoup
import pandas as pd
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

# URL config
global_url = "https://fr.wikipedia.org/wiki/" # Using french wikipedia for french personalities
headers = {'User-Agent': 'fetchFrenchPresidents'}
presidents = []

# Using  data.gouv.fr to obtain GPS localisation and administrative info of each city
def get_geo_data(city_name):
    if city_name == "N/A":
        return None
    
    base_url = "https://api-adresse.data.gouv.fr/search/"
    params = {'q': city_name, 'limit': 1}
    
    try:
        response = requests.get(base_url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['features']:
                best_result = data['features'][0]
                properties = best_result['properties']
                score = properties.get('score', 0)
                            
                # Confidence threshold: a low score indicate foreign pob
                if score < 0.6:
                    return {
                        "lon": None, "lat": None,
                        "dep_num": "foreign", "dep_name": "foreign", "region": "foreign"
                    }

                geom = best_result['geometry']['coordinates']
                context = properties.get('context', '')
                parts = context.split(',')
                            
                return {
                    "lon": geom[0],
                    "lat": geom[1],
                    "dep_num": parts[0] if len(parts) > 0 else None,
                    "dep_name": parts[1].strip() if len(parts) > 1 else None,
                    "region": parts[-1].strip() if len(parts) > 0 else None
            }
    except Exception:
        pass
    return None

# Reading our list of presidents
with open('/Users/eyquem/Desktop/LeadersMap/sources/presidents_list.txt', 'r', encoding='utf-8') as f:
    raw_list = [line.strip() for line in f if line.strip()]
    presidents_list = list(dict.fromkeys(raw_list)) # Removing duplicates before scrapping

for president in presidents_list:
    # Formatting
    url_name = president.replace(" ", "_")
    url = f"{global_url}{url_name}"

    try:
        page = requests.get(url, headers=headers)
        if page.status_code != 200:
            print(f"Error for {president}: couldn't find wikipedia page.")
            continue
            
        soup = BeautifulSoup(page.content, 'html.parser')

        # Finding name as the title of the page
        name = soup.find("h1", {"id": "firstHeading"}).text.strip()
        # Finding place and date of birth from the infobox
        infobox = soup.find("table", {"class": "infobox"})

        temp_dict = {
            "name": name,
            "tag": "president",
            "dob": "N/A",
            "pob": "N/A",
            "dep_num": None,
            "dep_name": None,
            "region": None,
            "lat": None,
            "lon": None
        }

        if infobox:
            rows_data = {}
            for row in infobox.find_all("tr"):
                header = row.find("th")
                value = row.find("td")
                if header and value:
                    rows_data[header.text.strip()] = value.text.strip()
            
            # Obtaining data from the infobox
            dob = rows_data.get("Date de naissance", "N/A")
            pob = rows_data.get("Lieu de naissance", "N/A")

            # Cleaning dob parenthesis (age) and only keeping the year
            dob = re.sub(r'\([^)]*\)', '', dob).strip()
            year = re.search(r'\d{4}', dob)
            dob = year.group(0) if year else "N/A"

            # Cleaning pob parenthesis (country)
            pob = re.sub(r'\([^)]*\)', '', pob).strip()
            
            temp_dict["dob"] = dob
            temp_dict["pob"] = pob

            # Geographic info
            geo = get_geo_data(pob)
            if geo:
                temp_dict.update({
                    "lat": geo["lat"],
                    "lon": geo["lon"],
                    "dep_num": geo["dep_num"],
                    "dep_name": geo["dep_name"],
                    "region": geo["region"]
                })
        
        presidents.append(temp_dict)
        time.sleep(0.1) # API rate limit

    except Exception as e:
        print(f"Error while processing {president} : {e}")

# Creating and organizing the df
df = pd.DataFrame(presidents)
df = df[['name', 'tag', 'dob', 'pob', 'dep_name', 'dep_num', 'region', 'lat', 'lon']]

print(df)

df.to_csv("/Users/eyquem/Desktop/LeadersMap/outputs/presidents_data.csv", index=False)