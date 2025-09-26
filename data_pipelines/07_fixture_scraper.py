import pandas as pd
from bs4 import BeautifulSoup
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from io import StringIO
import logging

def get_html_with_selenium(url: str) -> str | None:
    """
    Fetches the full HTML content of a page using Selenium to handle JavaScript rendering.
    """
    options = Options()
    options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = None
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "stats_table")))
        time.sleep(2)
        return driver.page_source
    except Exception as e:
        logging.error(f"An error occurred during Selenium execution for URL {url}: {e}")
        return None
    finally:
        if driver:
            driver.quit()

def main():
    """
    Scrapes and cleans the full Premier League fixture list for multiple seasons from FBREF.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # --- Configuration ---
    SEASONS_TO_SCRAPE = {
        "2024-2025": "https://fbref.com/en/comps/9/2024-2025/schedule/2024-2025-Premier-League-Scores-and-Fixtures",
        "2025-2026": "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"
    }
    OUTPUT_DIR = "raw_data"
    MASTER_OUTPUT_FILE = "fixtures_master.csv"
    
    all_fixtures_dfs = []

    for season, url in SEASONS_TO_SCRAPE.items():
        logging.info(f"--- Scraping fixtures for season: {season} ---")
        html_content = get_html_with_selenium(url)
        
        if not html_content:
            logging.error(f"Failed to retrieve HTML for {season}. Skipping.")
            continue

        soup = BeautifulSoup(html_content, 'html.parser')
        table = soup.find('table', {'class': 'stats_table'})
        
        if not table:
            logging.error(f"Could not find fixture table for {season}. Skipping.")
            continue
            
        df = pd.read_html(StringIO(str(table)))[0]
        
        # --- Enriched Data Extraction ---
        required_cols = ['Wk', 'Date', 'Home', 'Score', 'Away', 'xG', 'xG.1']
        df = df[required_cols]
        df = df.rename(columns={'xG': 'Home_xG', 'xG.1': 'Away_xG'})
        
        # --- Advanced Cleaning ---
        # Handle rows that are not matches (like mid-table headers)
        df = df.dropna(subset=['Wk'])
        df = df[pd.to_numeric(df['Wk'], errors='coerce').notna()]
        df['Wk'] = df['Wk'].astype(int)

        # Split the score into Home and Away goals
        score_split = df['Score'].str.split(r'[-–]', regex=True, expand=True)
        df['Home_Goals'] = pd.to_numeric(score_split[0], errors='coerce')
        df['Away_Goals'] = pd.to_numeric(score_split[1], errors='coerce')
        
        # Convert xG to numeric, handling missing values for future games
        df['Home_xG'] = pd.to_numeric(df['Home_xG'], errors='coerce')
        df['Away_xG'] = pd.to_numeric(df['Away_xG'], errors='coerce')

        # Add season identifier and reorder columns for readability
        df['Season'] = season
        final_cols = ['Season', 'Wk', 'Date', 'Home', 'Away', 'Home_Goals', 'Away_Goals', 'Home_xG', 'Away_xG']
        df = df[final_cols]
        
        all_fixtures_dfs.append(df)
        logging.info(f"Successfully processed {len(df)} matches for {season}.")
        
    # --- Combine, Sort, and Save Master File ---
    if all_fixtures_dfs:
        master_df = pd.concat(all_fixtures_dfs, ignore_index=True)
        master_df = master_df.sort_values(by=['Season', 'Wk'], ascending=[True, True])
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        master_output_path = os.path.join(OUTPUT_DIR, MASTER_OUTPUT_FILE)
        master_df.to_csv(master_output_path, index=False)
        logging.info(f"\n--- Master Fixture File Created ---")
        logging.info(f"Combined and cleaned data for {len(all_fixtures_dfs)} seasons.")
        logging.info(f"Master file saved to: {master_output_path}")
    else:
        logging.warning("No data was scraped. Master file not created.")

if __name__ == '__main__':
    main()

