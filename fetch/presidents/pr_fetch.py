from bs4 import BeautifulSoup
import utils.utils as utils
import pandas as pd
import requests
import socket
import time
import re

# Network config
utils.force_ipv4()

# URL config
global_url = "https://fr.wikipedia.org/wiki/" # Using french wikipedia for french personalities
headers = {'User-Agent': 'fetchFrenchPresidents'}
presidents = []

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
            geo = utils.finding_geo(pob)
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