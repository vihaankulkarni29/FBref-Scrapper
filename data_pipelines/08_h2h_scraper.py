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
import random

def get_html_with_selenium(url: str) -> str | None:
    """Fetches the full HTML content of a page using Selenium with maximum stealth options."""
    options = Options()
    options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    
    # --- MAXIMUM STEALTH PROTOCOL ---
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1200")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36")
    
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = None
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.stats_table")))
        time.sleep(3)
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
    # Corrected Squad IDs and URL-friendly names
    TEAMS_CONFIG = {
        "Arsenal": ("18bb7c10", "Arsenal"), "Aston Villa": ("8602292d", "Aston-Villa"), 
        "Bournemouth": ("4ba7cbea", "Bournemouth"), "Brentford": ("cd051869", "Brentford"), # CORRECTED SQUAD ID
        "Brighton": ("d07537b9", "Brighton-and-Hove-Albion"), "Chelsea": ("cff3d9bb", "Chelsea"),
        "Crystal Palace": ("47c64c55", "Crystal-Palace"), "Everton": ("d3fd31cc", "Everton"), 
        "Fulham": ("fd962109", "Fulham"), "Ipswich Town": ("c477b224", "Ipswich-Town"), 
        "Leicester City": ("a2d435b3", "Leicester-City"), "Liverpool": ("822bd0ba", "Liverpool"),
        "Manchester City": ("b8fd03ef", "Manchester-City"), "Manchester Utd": ("19538871", "Manchester-United"),
        "Newcastle Utd": ("b2b47a98", "Newcastle-United"), "Nott'ham Forest": ("e4a775cb", "Nottingham-Forest"),
        "Southampton": ("33c895d4", "Southampton"), "Tottenham": ("361ca564", "Tottenham-Hotspur"),
        "West Ham": ("7c21e445", "West-Ham-United"), "Wolves": ("8cec06e1", "Wolverhampton-Wanderers")
    }
    SEASONS_TO_SCRAPE = ["2023-2024", "2024-2025"]
    OUTPUT_DIR = "raw_data/h2h"
    MAX_RETRIES = 3
    RETRY_DELAY = 10
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for team_display_name, (squad_id, url_name) in TEAMS_CONFIG.items():
        for season in SEASONS_TO_SCRAPE:
            output_filename = f"{team_display_name.replace(' ', '_')}_{season}_h2h.csv"
            output_path = os.path.join(OUTPUT_DIR, output_filename)

            if os.path.exists(output_path):
                logging.info(f"Data for {team_display_name}, {season} already exists. Skipping.")
                continue

            url = f"https://fbref.com/en/squads/{squad_id}/{season}/matchlogs/all_comps/schedule/{url_name}-Scores-and-Fixtures-All-Competitions"
            
            for attempt in range(MAX_RETRIES):
                logging.info(f"Scraping H2H data for: {team_display_name}, {season} (Attempt {attempt + 1}/{MAX_RETRIES})")
                html_content = get_html_with_selenium(url)
                
                if html_content:
                    break 
                
                logging.warning(f"Failed to get HTML on attempt {attempt + 1}. Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            
            if not html_content:
                logging.error(f"Failed to get HTML for {team_display_name}, {season} after {MAX_RETRIES} attempts. Skipping.")
                continue

            soup = BeautifulSoup(html_content, 'html.parser')
            table = soup.find('table', {'class': 'stats_table'})
            
            if not table:
                logging.warning(f"No match log table found for {team_display_name}, {season}. Skipping.")
                continue
                
            df = pd.read_html(StringIO(str(table)))[0]
            
            df = df[['Date', 'Comp', 'Opponent', 'Result', 'GF', 'GA']]
            df.columns = ['Date', 'Competition', 'Opponent', 'Result', 'Goals_For', 'Goals_Against']
            df_cleaned = df.dropna(subset=['Date', 'Opponent']).copy()
            df_cleaned = df_cleaned[df_cleaned['Date'] != 'Date']
            
            df_cleaned.to_csv(output_path, index=False)
            logging.info(f"Successfully saved raw H2H data to {output_path}")
            
            human_delay = random.uniform(5, 10)
            logging.info(f"Pausing for {human_delay:.2f} seconds...")
            time.sleep(human_delay)

    logging.info("\n--- H2H Scraping Mission Complete ---")

if __name__ == '__main__':
    main()

