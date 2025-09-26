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
    """Fetches the full HTML content of a page using Selenium."""
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
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "matchlogs_for")))
        time.sleep(2)
        return driver.page_source
    except Exception as e:
        logging.error(f"Selenium error for URL {url}: {e}")
        return None
    finally:
        if driver:
            driver.quit()

def main():
    """Scrapes all-competition match logs for all Premier League teams for specified seasons."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # --- Configuration ---
    TEAMS_CONFIG = {
        "Arsenal": "18bb7c10", "Aston Villa": "8602292d", "Bournemouth": "4ba7c610",
        "Brentford": "cd051869", "Brighton": "d07537b9", "Chelsea": "cff3d9bb",
        "Crystal Palace": "47c64c55", "Everton": "d3fd31cc", "Fulham": "fd962109",
        "Ipswich Town": "c477b224", "Leicester City": "a2d435b3", "Liverpool": "822bd0ba",
        "Manchester City": "b8fd03ef", "Manchester Utd": "19538871", "Newcastle Utd": "b2b47a98",
        "Nott'ham Forest": "e4a775cb", "Southampton": "33c895d4", "Tottenham": "361ca564",
        "West Ham": "7c21e445", "Wolves": "8cec06e1"
    }
    SEASONS_TO_SCRAPE = ["2023-2024", "2024-2025"]
    OUTPUT_DIR = "raw_data/h2h"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for season in SEASONS_TO_SCRAPE:
        logging.info(f"--- Starting H2H Scrape for Season: {season} ---")
        for team_name, squad_id in TEAMS_CONFIG.items():
            
            url = f"https://fbref.com/en/squads/{squad_id}/{season}/matchlogs/all_comps/{team_name}-Match-Logs-All-Competitions"
            logging.info(f"Scraping H2H data for: {team_name}")
            
            html_content = get_html_with_selenium(url)
            
            if not html_content:
                logging.error(f"Failed to get HTML for {team_name}, {season}. Skipping.")
                continue

            soup = BeautifulSoup(html_content, 'html.parser')
            table = soup.find('table', {'id': 'matchlogs_for'})
            
            if not table:
                logging.warning(f"No match log table found for {team_name}, {season}. Skipping.")
                continue
                
            df = pd.read_html(StringIO(str(table)))[0]
            
            # --- ROBUST CLEANING FIX ---
            # 1. Flatten the multi-level column headers
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.map('_'.join).str.strip()
            
            # 2. Select the columns we need using a flexible approach
            # Find the actual column names by looking for keywords
            date_col = [col for col in df.columns if 'Date' in col][0]
            comp_col = [col for col in df.columns if 'Comp' in col][0]
            opp_col = [col for col in df.columns if 'Opponent' in col][0]
            result_col = [col for col in df.columns if 'Result' in col][0]
            gf_col = [col for col in df.columns if 'GF' in col][0]
            ga_col = [col for col in df.columns if 'GA' in col][0]
            
            # Create a new DataFrame with just these columns
            df_selected = df[[date_col, comp_col, opp_col, result_col, gf_col, ga_col]].copy()
            
            # 3. Rename them to a clean, final format
            df_selected.columns = ['Date', 'Competition', 'Opponent', 'Result', 'Goals_For', 'Goals_Against']
            
            # 4. Drop empty/header rows
            df_cleaned = df_selected.dropna(subset=['Date']).copy()
            
            # Save the raw file
            output_filename = f"{team_name.replace(' ', '_')}_{season}_h2h.csv"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            df_cleaned.to_csv(output_path, index=False)
            logging.info(f"Successfully saved raw H2H data to {output_path}")

    logging.info("\n--- H2H Scraping Mission Complete ---")

if __name__ == '__main__':
    main()

