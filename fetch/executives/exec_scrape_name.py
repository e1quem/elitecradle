from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from pathlib import Path
import utils as utils
import pandas as pd
import requests
import random
import socket
import time

# Network config
utils.force_ipv4()
base_path = Path("~/elitecradle").expanduser()

def format_name(name):
    # Deleting parenthesis
    if '(' in name:
        name = name.split('(')[0].strip()

    parts = name.split()
    if len(parts) >= 2:
        surname = parts[-1].capitalize()
        name = ' '.join(parts[:-1])
        name = '-'.join([part.capitalize() for part in name.replace(' ', '-').split('-')])

        # Handling particles names
        name = name.lower().title()
        name = name.replace(' De ', ' de ')
        name = name.replace(' Du ', ' du ')
        name = name.replace(' La ', ' la ')

        return f"{surname} {name}"
    else:
        return name.capitalize()

def extract_exec(driver, url):
    # Extracting the name of CAC40 administrators using Chrome scraping on pappers.fr
    driver.get(url)
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))#, h1.small-text"))
        )
    except Exception as e:
        print(f"Error loading {url}: {e}")
        return []
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Obtaining the name of the company
    firm = soup.find('h1', class_=['big-text', 'small-text']).get_text(strip=True)

    # Extracting list of top executives
    exec = []
    section = soup.find('section', id='dirigeants')
    if section:
        for li in section.select('ul#representants-container li.dirigeant'):
            name_div = li.find('div', class_='nom')
            if name_div:
                name = name_div.find('a').get_text(strip=True)
                qualite = li.find('span', class_='qualite').get_text(strip=True)

                # We ignore audit firms
                if 'commissaire' not in qualite.lower():
                    name_formatte = format_name(name)
                    exec.append((name_formatte, firm))
    return exec


def main():
    input_file = base_path / "fetch/executives/src/cac_list.txt"
    output_file = base_path / "fetch/executives/interim/execs.csv"

    # Navigator config
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized')
    driver = uc.Chrome(options=options, version_main = 145)

    all_exec = []
    
    try:
        with open(input_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]
        for url in urls:
            print(f"Current URL: {url}...")
            try:
                res = extract_exec(driver, url)
                all_exec.extend(res)
            except Exception as e:
                print(f"Error on {url} : {e}")
            time.sleep(random.uniform(2, 4))
    finally:
        driver.quit()

    df = pd.DataFrame(all_exec, columns=['name', 'firm'])
    df.to_csv(output_file, index=False)
    print(f"Done. {len(df)} staff found.")

if __name__ == "__main__":
    main()