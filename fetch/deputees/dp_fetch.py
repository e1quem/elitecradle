from bs4 import BeautifulSoup
import pandas as pd
import requests
import re

# Using data.gouv.fr API to obtain GPS localisation, dept number and region of each pob
def get_geo_data(pob, dept_ob):
    # We skip the call if the pob is foreign
    if pob == "foreign" or pob == "N/A":
        return None
    
    base_url = "https://api-adresse.data.gouv.fr/search/"
    # We use the dept_ob for more accuracy in our query
    query = f"{pob} {dept_ob}"
    params = {'q': query, 'limit': 1}
    
    try:
        response = requests.get(base_url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data['features']:
                best_result = data['features'][0]
                properties = best_result['properties']

                geom = best_result['geometry']['coordinates']
                context = properties.get('context', '')
                parts = context.split(',')
                            
                return {
                    "lon": geom[0],
                    "lat": geom[1],
                    "dep_num": parts[0].strip() if len(parts) > 0 else None,
                    "dep_name": parts[1].strip() if len(parts) > 1 else None,
                    "region": parts[-1].strip() if len(parts) > 2 else None,
                    "confidence": round(properties.get('score', 0), 3)
                }
    except Exception:
        pass
    return None

def get_depute_data_by_id(id):
    url = f"https://www2.assemblee-nationale.fr/sycomore/fiche/{id}"
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Name (H1)
        name = " ".join(soup.find("h1").get_text().split()) if soup.find("h1") else "N/A"

        # dob and pob: "Informations générales"
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
                    
                    # Searching the pob (pattern between à and the closing parenthesis)
                    # The parenthesis either contains (Department_name - France) or (Country_name)
                    pob_match = re.search(r' à (.*?) \((.*?)\)', text)
                    if pob_match:
                        city_name = pob_match.group(1).strip()
                        bracket_content = pob_match.group(2)

                        if "France" in bracket_content:
                            # We extract the city name and the department name (before " - France")
                            pob = city_name
                            dept_ob = bracket_content.split(" - France")[0].strip()
                            geo_info = get_geo_data(pob, dept_ob)
                        else:
                            # France not mentioned : considered foreign
                            # Note : this excludes old colonies, and eventually DOM-TOMs depending on how the AN's website present these cities.
                            pob, dept_ob = "foreign", "foreign"
                    else:
                        pob, dept_ob = "foreign", "foreign"
                    break


        return {
            "name": name,
            "tag": "depute",
            "dob": dob,
            "pob": pob,
            "dept_ob": geo_info["dep_name"] if geo_info else ("foreign" if pob == "foreign" else None),
            "dept_num": geo_info["dep_num"] if geo_info else ("foreign" if pob == "foreign" else None),
            "region": geo_info["region"] if geo_info else ("foreign" if pob == "foreign" else None),
            "lat": geo_info["lat"] if geo_info else None,
            "lon": geo_info["lon"] if geo_info else None,
            "confidence" : geo_info["confidence"] if geo_info else None, 
            "id": id
        }

    except Exception as e:
        print(f"Error on {id}: {e}")
        return None
    
# Loading the CSV previously obtained
df = pd.read_csv("/Users/eyquem/Desktop/LeadersMap/outputs/dp_id.csv", sep=None, engine='python')

#df_subset = df.head(100)
new_results = []
#total_dp = len(df_subset)
total_dp = len(df)


#for index, row in df_subset.iterrows():
for index, row in df.iterrows():
    id = str(row['id'])
    
    data = get_depute_data_by_id(id)
    
    if data:
        print(f"\r\033[K[{index+1}/{total_dp}] {data['name']}...", end="", flush=True)
        new_results.append(data)
    else:
        print(f"\r\033[K[{index+1}/{total_dp}] ID {id} : Error fetching data.", end="", flush=True)

df_details = pd.DataFrame(new_results)

# Results
print(df_details.head())

# Saving as CSV
output_path = "/Users/eyquem/Desktop/LeadersMap/outputs/dp_raw.csv"
df_details.to_csv(output_path, index=False, encoding='utf-8')