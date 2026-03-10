from selenium.webdriver.support.ui import WebDriverWait
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import pandas as pd
import requests
import random
import socket
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

# Network config
def force_ipv4():
    old_getaddrinfo = socket.getaddrinfo
    def new_getaddrinfo(*args, **kwargs):
        responses = old_getaddrinfo(*args, **kwargs)
        return [r for r in responses if r[0] == socket.AF_INET]
    socket.getaddrinfo = new_getaddrinfo
force_ipv4()

def format_name(name):
    # Deleting parenthesis
    if '(' in name:
        name = name.split('(')[0].strip()

    parts = name.split()
    if len(parts) >= 2:
        surname = parts[-1].capitalize()
        name = ' '.join(parts[:-1])

        name = '-'.join(
            [part.capitalize() for part in name.replace(' ', '-').split('-')]
        )

        # Handling particles names
        name = name.lower().title()
        name = name.replace(' De ', ' de ')
        name = name.replace(' Du ', ' du ')
        name = name.replace(' La ', ' la ')

        return f"{surname} {name}"
    else:
        return name.capitalize()

def extract_exec(driver, url):
    driver.get(url)

    #time.sleep(random.uniform(3, 6))

    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))#, h1.small-text"))
        )
    except Exception as e:
        print(f"Error loading {url}: {e}")
        return []

        
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Obtaining name of the company
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
    input_file = "/Users/eyquem/Desktop/LeadersMap/sources/cac_list.txt"
    output_file = "/Users/eyquem/Desktop/LeadersMap/outputs/cac_staff.csv"
    
    # Navigator config
    options = uc.ChromeOptions()

    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized')
    #options.add_argument('--headless') # Hiding the opened window

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
            
            # Break between each url
            time.sleep(random.uniform(2, 4))

    finally:
        driver.quit()

    df = pd.DataFrame(all_exec, columns=['name', 'firm'])
    df.to_csv(output_file, index=False)
    print(f"Done. {len(df)} staff found.")

if __name__ == "__main__":
    main()