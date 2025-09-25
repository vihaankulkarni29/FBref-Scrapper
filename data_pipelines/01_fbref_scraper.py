import os
import time
import random
import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup, Comment
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import List, Dict, Optional

# --- All helper functions (get_proxy_list, get_random_user_agent, etc.) remain the same ---

def get_proxy_list(filepath: str) -> List[str]:
    """Reads a list of proxies from a text file."""
    if not os.path.exists(filepath):
        print(f"Warning: Proxy file not found at {filepath}. Running without proxies.")
        return []
    with open(filepath, 'r') as f:
        proxies = [line.strip() for line in f if line.strip()]
    print(f"Loaded {len(proxies)} proxies.")
    return proxies

def get_random_user_agent() -> str:
    """Returns a random User-Agent string from a predefined list."""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/109.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0',
    ]
    return random.choice(user_agents)

def setup_webdriver(proxy: Optional[str], user_agent: str) -> webdriver.Chrome:
    """Configures and returns a headless Selenium WebDriver instance."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1200")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    if proxy:
        chrome_options.add_argument(f'--proxy-server={proxy}')
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def fetch_page_source(url: str, proxies: List[str], max_retries: int = 3) -> Optional[str]:
    """
    Fetches the full page source of a URL using Selenium with proxy/UA rotation and retry logic.
    """
    last_exception = None
    for attempt in range(max_retries):
        print(f"Attempt {attempt + 1} of {max_retries} to fetch {url}")
        proxy = random.choice(proxies) if proxies else None
        user_agent = get_random_user_agent()
        driver = None
        try:
            driver = setup_webdriver(proxy, user_agent)
            driver.get(url)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.table_container"))
            )
            return driver.page_source
        except Exception as e:
            print(f"An error occurred on attempt {attempt + 1}: {e}")
            last_exception = e
            time.sleep(5 * (attempt + 1))
        finally:
            if driver:
                driver.quit()
    print(f"Failed to fetch URL after {max_retries} attempts. Last error: {last_exception}")
    return None

def parse_tables_from_html(html: str, table_ids: List[str]) -> Dict[str, pd.DataFrame]:
    """Parses specified tables from HTML source, handling commented-out tables."""
    soup = BeautifulSoup(html, 'html.parser')
    dataframes = {}
    for table_id in table_ids:
        table_div = soup.find('div', id=f'div_{table_id}')
        if not table_div:
            print(f"Warning: Could not find div for table_id '{table_id}'. Skipping.")
            continue
        comment = table_div.find(string=lambda text: isinstance(text, Comment))
        if comment:
            table_soup = BeautifulSoup(comment, 'html.parser')
            table = table_soup.find('table', id=table_id)
        else:
            table = table_div.find('table', id=table_id)
        if table:
            # FIX 1: Use StringIO to handle pandas FutureWarning
            df = pd.read_html(StringIO(str(table)))[0]
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(col).strip() for col in df.columns.values]
            
            # FIX 2: Dynamically find the player column to prevent KeyError
            player_col_name = None
            if 'Player_Player' in df.columns:
                player_col_name = 'Player_Player'
            else:
                # Find the first column that contains 'Player' as a fallback
                possible_cols = [col for col in df.columns if 'Player' in col]
                if possible_cols:
                    player_col_name = possible_cols[0]

            if player_col_name:
                # Remove junk rows using the dynamically found player column
                df = df[~df[player_col_name].str.contains('Player', na=False)]
                df = df.dropna(subset=[player_col_name])
                print(f"Successfully parsed and cleaned table: {table_id}")
            else:
                print(f"Warning: Could not find a 'Player' column for table '{table_id}'. Skipping row cleaning.")
            
            dataframes[table_id] = df
        else:
            print(f"Warning: Could not find table '{table_id}' within its div.")
    return dataframes

def main():
    """Main execution function."""
    # --- Configuration ---
    SEASONS = {
        "2024-2025": "https://fbref.com/en/comps/9/2024-2025/stats/2024-2025-Premier-League-Stats",
        "2023-2024": "https://fbref.com/en/comps/9/2023-2024/stats/2023-2024-Premier-League-Stats",
    }
    
    # --- THIS IS THE UPGRADE ---
    # We've added the new tables to our scrape list.
    TABLES_TO_SCRAPE = [
        'stats_standard',    # Still need for Gls, Asts, Mins
        'stats_shooting',    # For Shots, SoT, npxG
        'stats_gca',         # For SCA, GCA
        'stats_possession'   # For Touches in Att Pen Area
    ]
    
    PROXIES_FILE = "proxies.txt"
    OUTPUT_DIR = "raw_data"

    # --- Execution (remains the same) ---
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    proxies = get_proxy_list(PROXIES_FILE)

    for season_name, url in SEASONS.items():
        print(f"\n--- Scraping Season: {season_name} ---")
        season_dir = os.path.join(OUTPUT_DIR, season_name)
        os.makedirs(season_dir, exist_ok=True)
        html_content = fetch_page_source(url, proxies)
        if html_content:
            tables = parse_tables_from_html(html_content, TABLES_TO_SCRAPE)
            if tables:
                for table_id, df in tables.items():
                    output_path = os.path.join(season_dir, f"{table_id}.csv")
                    df.to_csv(output_path, index=False)
                    print(f"Saved data to {output_path}")
            else:
                print(f"No tables could be parsed for season {season_name}.")
        else:
            print(f"Failed to retrieve page source for season {season_name}.")
        sleep_time = random.uniform(4, 10)
        print(f"Sleeping for {sleep_time:.2f} seconds before next season...")
        time.sleep(sleep_time)
    print("\n--- Scraping process complete. ---")

if __name__ == '__main__':
    main()