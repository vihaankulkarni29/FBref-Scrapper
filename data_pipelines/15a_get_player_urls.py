import pandas as pd
import os
import logging
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def get_html_with_selenium(url: str, wait_condition) -> str | None:
    """Fetches the full HTML content of a page using Selenium."""
    # This robust helper function remains our core browser engine.
    options = Options()
    options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
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
        WebDriverWait(driver, 25).until(wait_condition)
        time.sleep(3) # Extra sleep for dynamic content
        return driver.page_source
    except Exception as e:
        logging.error(f"Selenium error for URL {url}: {e}")
        return None
    finally:
        if driver:
            driver.quit()

def main():
    """
    Scrapes per-match player performance data from SofaScore by iterating through a fixture list.
    This is a resumable, fixture-centric approach.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # --- Configuration ---
    FIXTURES_FILE = "processed_data/fixtures_master.csv"
    SEASON_TO_SCRAPE = "2024-2025"
    OUTPUT_DIR = "raw_data/sofascore_match_stats" # New dedicated directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if not os.path.exists(FIXTURES_FILE):
        logging.error(f"Fixtures file not found at {FIXTURES_FILE}. Aborting.")
        return

    fixtures_df = pd.read_csv(FIXTURES_FILE)
    # Filter for the target season and only matches that have been played (have a score)
    target_fixtures = fixtures_df[fixtures_df['Season'] == SEASON_TO_SCRAPE].dropna(subset=['Home_Goals'])
    logging.info(f"Found {len(target_fixtures)} historical matches for season {SEASON_TO_SCRAPE}.")

    for index, fixture in target_fixtures.iterrows():
        home_team = fixture['Home']
        away_team = fixture['Away']
        match_date = pd.to_datetime(fixture['Date']).strftime('%Y-%m-%d')
        
        output_filename = f"{match_date}_{home_team.replace(' ', '_')}_vs_{away_team.replace(' ', '_')}.csv"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        if os.path.exists(output_path):
            logging.info(f"Match data for {home_team} vs {away_team} on {match_date} already exists. Skipping.")
            continue

        logging.info(f"--- Scouting Match: {home_team} vs {away_team} ---")
        
        # --- NEW FIXTURE-CENTRIC LOGIC ---
        # 1. Search for the match on SofaScore
        search_url = f"https://www.sofascore.com/search/results?q={home_team.replace(' ', '+')}+{away_team.replace(' ', '+')}"
        # Wait for a search result link to appear
        wait_condition = EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/football/']"))
        search_html = get_html_with_selenium(search_url, wait_condition)

        if not search_html:
            logging.warning(f"Could not perform search for match: {home_team} vs {away_team}. Skipping.")
            continue

        # 2. Find the correct match link from the search results
        soup = BeautifulSoup(search_html, 'html.parser')
        match_links = soup.find_all('a', href=lambda href: href and '/football/' in href)
        
        match_page_url = None
        for link in match_links:
            # Heuristic: Find a link containing both team names
            if home_team.lower() in link.text.lower() and away_team.lower() in link.text.lower():
                match_page_url = "https://www.sofascore.com" + link['href']
                logging.info(f"Found match page URL: {match_page_url}")
                break
        
        if not match_page_url:
            logging.warning(f"Could not find a matching page link for {home_team} vs {away_team}. Skipping.")
            continue

        # --- Placeholder for the complex data extraction from the match page ---
        # This part will be built out next, but we have solved the primary navigation problem.
        placeholder_data = {
            'player_name': ['Player A', 'Player B'],
            'sofascore_rating': [7.5, 8.1],
            'xG': [0.8, 1.2], 'xA': [0.3, 0.1] 
            # ... etc. for all players and all stats in the match
        }
        match_stats_df = pd.DataFrame(placeholder_data)
        match_stats_df.to_csv(output_path, index=False)
        logging.info(f"Successfully scraped and saved placeholder data for {home_team} vs {away_team}.")
        # --- End of placeholder ---
        
        time.sleep(random.uniform(5, 10))

    logging.info("\n--- SofaScore Match Scraping Complete ---")

if __name__ == '__main__':
    main()
