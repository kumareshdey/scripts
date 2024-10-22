import requests
from retry import retry
from setup import log
from bs4 import BeautifulSoup
from credential import SCRAPEOPS
import pandas as pd
import os


@retry(tries=2, delay=1)
def proxied_request(url):
    PROXY_URL = 'https://proxy.scrapeops.io/v1/'
    response = requests.get(
        url=PROXY_URL,
        params={
            'api_key': SCRAPEOPS,
            'url': url,
            'country': 'us',
            'bypass': 'cloudflare_level_3',
        },
        # timeout=60
    )
    if response.status_code != 200:
        log.error(f"Could not get successful response. Status code {response.status_code}. {response.text}")
        raise Exception(f"Request failed. Status code {response.status_code}")
    log.info(f"Got successful response from {url}")
    return response

street_suffixes = {
    'boulevard': 'blvd',
    'street': 'st',
    'road': 'rd',
    'avenue': 'ave',
    'drive': 'dr',
    'court': 'ct',
    'lane': 'ln',
    'place': 'pl',
    'terrace': 'ter',
    'circle': 'cir',
    'square': 'sq'
}

# Function to standardize address suffixes
def standardize_suffix(address):
    words = address.split()
    new_words = []
    log.info(f"Original address: {address}")
    for i, word in enumerate(words):
        # Normalize the word to lowercase for reliable matching
        normalized_word = word.lower().replace('.', '')  # Remove periods and convert to lowercase
        if normalized_word in street_suffixes:
            log.info(f"Replacing '{word}' with '{street_suffixes[normalized_word]}'")
            new_words.append(street_suffixes[normalized_word])
        else:
            new_words.append(word)
    new_address = ' '.join(new_words)
    log.info(f"Standardized address: {new_address}")
    return new_address

def generate_url(row):
    address = standardize_suffix(row['Street']).replace(" ", "-").lower()
    city = row['City'].replace(" ", "-").lower()
    return f"https://www.fastpeoplesearch.com/address/{address}_{city}-{row['State/Region'].lower()}"

def current_home_address_matches_address_searched(current_address, address):
    return address.lower() in current_address.lower()

def any_prior_home_address_matches_address_searched(prev_addresses, address):
    return any(address.lower() in prev_address.lower() for prev_address in prev_addresses)

def save_data(rows, file_name):
    result_excel_file_path = "/home/ubuntu/scripts/result_file/" + file_name
    df = pd.DataFrame(rows).astype(str)  # Convert all data to string
    
    if os.path.exists(result_excel_file_path):
        existing_df = pd.read_excel(
            result_excel_file_path, 
            names=["Street", "City", "State/Region", "URL", "Name", "Age", "Current Home Address", 
                   "Current Home Address Matches Address Searched", 
                   "Any Prior Home Address Matches Address Searched", 
                   "Success"], 
            engine="openpyxl"
        ).astype(str)  # Ensure existing data is treated as string too
        existing_df = pd.concat([existing_df, df], ignore_index=True)
        df = existing_df
    else:
        with open(result_excel_file_path, "w"):
            pass
        
    df.to_excel(result_excel_file_path, index=False)
    log.info(f'Saved {len(rows)} entries in {result_excel_file_path}')


def scrape_single_page_data(final_url, row):
    per_page_data = []
    try:
        response = proxied_request(final_url)
    except KeyboardInterrupt:
        log.error("Keyboard interruption during scraping.")
        raise
    except Exception as e:
        log.error(f"Exception during scraping page data: {e}")
        return [{
            "Street": row["Street"],
            "City": row["City"],
            "State/Region": row['State/Region'],
            "URL": final_url,
            "Name": '',
            "Age": '',
            "Current Home Address": '',
            "Current Home Address Matches Address Searched": '' ,
            "Any Prior Home Address Matches Address Searched": '',
            "Success": "False"
        }]
    
    soup = BeautifulSoup(response.text, 'html.parser')
    with open("output.html", "w", encoding="utf-8") as file:
        file.write(soup.prettify()) 
    table = soup.find('div', class_='people-list')
    if table:
        cards = table.find_all('div', class_='card-block')
        
        for card in cards:
            try:
                try:
                    name = card.find('h3', text='Full Name:').next_sibling.strip()
                except:
                    name = card.find('span', class_='larger').text.strip()
                try:
                    age = card.find('h3', text='Age:').next_sibling.strip()
                except:
                    age = ''
                try:
                    current_address = card.find('h3', text='Current Home Address:').find_next('a').text.strip()
                except:
                    current_address = ''
                try:
                    prev_addresses = [a.text.strip() for a in card.find_all('div', class_='col-sm-12 col-md-6')]
                except:
                    prev_addresses = []
                # name, age, current_address, prev_addresses = '', '', '', []
                # if _name:
                #     name = _name.get_text()
                # if _age:
                #     age = _age.get_text()
                # if _current_address:
                #     current_address = _current_address.find('a', class_='address').get_text()
                # if _prev_address:
                #     prev_addresses = [prev.find('a', class_='address').get_text() for prev in _prev_address]

                new_row = {
                    "Street": row["Street"],
                    "City": row["City"],
                    "State/Region": row['State/Region'],
                    "URL": final_url,
                    "Name": name,
                    "Age": str(age),
                    "Current Home Address": current_address,
                    "Current Home Address Matches Address Searched": str(current_home_address_matches_address_searched(current_address, row["Street"])),
                    "Any Prior Home Address Matches Address Searched": str(any_prior_home_address_matches_address_searched(prev_addresses, row["Street"])),
                    "Success": str(True)
                }
                per_page_data.append(new_row)
            except Exception as e:
                log.error(f"Exception during data extraction from card: {e}")
                pass
    return per_page_data

def url_is_present_in_file(url, file_name):
    result_excel_file_path = "/home/ubuntu/scripts/result_file/" + file_name
    try:
        data = pd.read_excel(result_excel_file_path)
        return url in data['URL'].values
    except:
        return False

def get_me_data(url, row, file_name):
    i = 1
    try:
        while True:
            final_url = f"{url}/page/{i}"
            if url_is_present_in_file(final_url, file_name):
                log.info(f"Skipping {final_url} because already scraped.")
                i += 1
                continue
            log.info(f"Scraping {final_url}")
            try:
                data = scrape_single_page_data(final_url, row)
                if not data:
                    break
                save_data(data, file_name)
            except KeyboardInterrupt:
                log.error("Keyboard interruption during pagination scraping.")
                raise
            except Exception as e:
                log.error(f"Error in scraping. {e}")
                pass
            i += 1
    except KeyboardInterrupt:
        log.error("Keyboard interruption. Exiting loop.")
        raise

if __name__ == '__main__':
    try:
        import sys
        file = sys.argv[1]
        df = pd.read_excel(file)
        for index, row in df.iterrows():
            url = generate_url(row)
            get_me_data(url, row, file.split('/')[-1])
    except KeyboardInterrupt:
        log.error("Keyboard interruption. Exiting the script.")
        sys.exit(1)