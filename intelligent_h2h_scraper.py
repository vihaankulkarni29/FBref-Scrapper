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
from config import *

def get_html_with_selenium(url: str) -> str | None:
    """Fetches the full HTML content of a page using Selenium with Ghost Protocol stealth options."""
    options = Options()

    # Set Chrome binary if configured and exists
    if CHROME_BINARY_PATH and os.path.exists(CHROME_BINARY_PATH):
        options.binary_location = CHROME_BINARY_PATH
    else:
        logging.warning("Chrome binary path not set or does not exist. Using default.")

    # --- GHOST PROTOCOL STEALTH UPGRADE ---
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")  # Recommended for headless
    options.add_argument("--window-size=1920,1200")  # Mimic standard desktop
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Advanced stealth options
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = None
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        # Execute script to hide webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        driver.get(url)
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "matchlogs_for")))
        time.sleep(3)  # Patient sleep after page load
        return driver.page_source
    except Exception as e:
        logging.error(f"Selenium error for URL {url}: {e}")
        return None
    finally:
        if driver:
            driver.quit()

def main():
    """Main execution loop for scraping H2H data."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for season in SEASONS_TO_SCRAPE:
        logging.info(f"--- Starting H2H Scrape for Season: {season} ---")
        for team_name, team_data in TEAMS_CONFIG.items():
            squad_id = team_data['id']
            team_slug = team_data['slug']

            output_filename = f"{team_name.replace(' ', '_')}_{season}_h2h.csv"
            output_path = os.path.join(OUTPUT_DIR, output_filename)

            if os.path.exists(output_path):
                logging.info(f"Data for {team_name}, {season} already exists. Skipping.")
                continue

            # Construct URL using Intelligent URL logic
            if season == MOST_RECENT_SEASON:
                url = f"https://fbref.com/en/squads/{squad_id}/matchlogs/all_comps/{team_slug}-Match-Logs-All-Competitions"
            else:
                url = f"https://fbref.com/en/squads/{squad_id}/{season}/matchlogs/all_comps/{team_slug}-Match-Logs-All-Competitions"

            logging.info(f"Scraping H2H data for: {team_name} from {url}")
            html_content = get_html_with_selenium(url)

            if html_content:
                logging.info(f"Successfully fetched HTML for {team_name}, {season}")
                # TODO: Parse and save data (to be implemented in next steps)
            else:
                logging.error(f"Failed to fetch HTML for {team_name}, {season}")

            # Human-like delay
            human_delay = random.uniform(5, 10)
            logging.info(f"Pausing for {human_delay:.2f} seconds to appear more human...")
            time.sleep(human_delay)

    logging.info("--- H2H Scraping Core Engine Complete ---")

if __name__ == '__main__':
    main()