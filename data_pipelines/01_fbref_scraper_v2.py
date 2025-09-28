import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import os
import time
import logging
from io import StringIO

def get_html_with_selenium(url: str, retries=3, delay=5) -> str | None:
    """Fetches HTML content using Selenium with stealth options and retries."""
    options = Options()
    if 'CHROME_BINARY' in os.environ:
        options.binary_location = os.environ['CHROME_BINARY']
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    for attempt in range(retries):
        driver = None
        try:
            service = ChromeService(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.get(url)
            WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.table_wrapper")))
            return driver.page_source
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                logging.error(f"All {retries} attempts failed for {url}.")
                return None
        finally:
            if driver:
                driver.quit()

def parse_and_save_table(html_content: str, table_id: str, output_path: str):
    """Parses a specific table from HTML and saves it to a CSV with clean headers."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    table = None
    table_div = soup.find('div', id=f'div_{table_id}')

    if table_div:
        from bs4 import Comment
        comment = table_div.find(string=lambda text: isinstance(text, Comment))
        if comment:
            comment_soup = BeautifulSoup(comment, 'html.parser')
            table = comment_soup.find('table', {'id': table_id})
        
        if not table:
            table = table_div.find('table', {'id': table_id})

    if table:
        # --- UPGRADED CLEANING LOGIC ---
        df = pd.read_html(StringIO(str(table)))[0]
        
        # 1. Robustly flatten MultiIndex headers if they exist
        if isinstance(df.columns, pd.MultiIndex):
            # The second level (index 1) contains the real column names
            df.columns = df.columns.get_level_values(1)
        
        # 2. Remove junk rows where 'Rk' is not a number (catches repeated headers)
        df = df[pd.to_numeric(df['Rk'], errors='coerce').notna()]
        
        # 3. Drop the 'Rk' column as it's just an index
        df = df.drop(columns=['Rk'])
        
        # 4. Drop any columns that are completely empty after parsing
        df = df.dropna(axis=1, how='all')
        
        df.to_csv(output_path, index=False)
        logging.info(f"Successfully parsed, cleaned, and saved table to {output_path}")
    else:
        logging.warning(f"Could not find table with ID: {table_id}")

def main():
    """Main execution function to scrape player data for the current season."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # --- Configuration for 2025-2026 Season ---
    SEASON = "2025-2026"
    SEASON_URL = "https://fbref.com/en/comps/9/stats/Premier-League-Stats" 
    TABLES_TO_SCRAPE = {
        "stats_standard": "standard_stats",
        "stats_shooting": "shooting_stats",
        "stats_passing": "passing_stats",
        "stats_gca": "gca_stats",
        "stats_defense": "defense_stats",
        "stats_possession": "possession_stats"
    }
    OUTPUT_DIR = f"raw_data/{SEASON}"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    logging.info(f"--- Scraping Player Data for Season: {SEASON} ---")
    html = get_html_with_selenium(SEASON_URL)
    
    if html:
        for table_id, filename_prefix in TABLES_TO_SCRAPE.items():
            output_file = f"{filename_prefix}_{SEASON}.csv"
            output_path = os.path.join(OUTPUT_DIR, output_file)
            parse_and_save_table(html, table_id, output_path)
    else:
        logging.error("Failed to retrieve main page HTML. Aborting.")

    logging.info("--- Current Season Scraping Complete ---")

if __name__ == '__main__':
    main()

