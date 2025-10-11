import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import logging
import os
import re
import functools

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
SEASON = "2024-2025"  # Specify the season
FIXTURES_FILE = f"fbref_data/fbref_fixtures_{SEASON}.csv"
OUTPUT_DIR = "sofascore_match_data"
SOFASCORE_SEARCH_URL = "https://www.sofascore.com/search"

def setup_driver():
    """Setup Selenium WebDriver with Ghost Protocol configuration."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def random_delay(min_delay=1, max_delay=3):
    """Add random delay."""
    time.sleep(random.uniform(min_delay, max_delay))

def retry_on_failure(max_retries=3, delay=5):
    """Decorator to retry function on failure."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logging.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(delay)
                    else:
                        raise
        return wrapper
    return decorator

def load_fixtures():
    """Load fixtures from CSV."""
    if not os.path.exists(FIXTURES_FILE):
        logging.error(f"Fixtures file {FIXTURES_FILE} not found.")
        return pd.DataFrame()
    df = pd.read_csv(FIXTURES_FILE)
    return df

@retry_on_failure()
def search_match_on_sofascore(driver, home_team, away_team, date):
    """Search for match on SofaScore and return the URL."""
    query = f"{home_team} vs {away_team} {date}"
    driver.get(f"{SOFASCORE_SEARCH_URL}?q={query.replace(' ', '%20')}")
    random_delay()

    try:
        # Wait for search results
        results = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".search-result"))  # Adjust selector
        )
        for result in results:
            # Check if the result matches the date
            if date in result.text:
                link = result.find_element(By.TAG_NAME, "a").get_attribute("href")
                return link
    except Exception as e:
        logging.warning(f"Search failed for {query}: {e}")
    return None

@retry_on_failure()
def scrape_match_data(driver, match_url, home_team, away_team, date):
    """Scrape data from a SofaScore match page."""
    driver.get(match_url)
    random_delay()

    # Click Statistics tab
    try:
        stats_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[text()='Statistics']"))  # Adjust XPath
        )
        stats_tab.click()
        random_delay()
    except Exception as e:
        logging.error(f"Failed to click Statistics tab: {e}")
        return pd.DataFrame()

    # Extract formations
    formations = extract_formations(driver)

    # Extract player stats
    players_data = []
    # Find all players, perhaps in lineup or stats sections
    player_elements = driver.find_elements(By.CSS_SELECTOR, ".player-row")  # Adjust selector
    for player_elem in player_elements:
        player_name = player_elem.find_element(By.CSS_SELECTOR, ".player-name").text
        # Click on player to get detailed stats
        player_elem.click()
        random_delay()

        # Extract stats from tabs
        stats = extract_player_stats(driver)

        # Extract heatmap center
        heatmap_center = extract_heatmap_center(driver)

        # Combine
        player_data = {
            'player_name': player_name,
            'home_team': home_team,
            'away_team': away_team,
            'date': date,
            'home_formation': formations.get('home'),
            'away_formation': formations.get('away'),
            **stats,
            **heatmap_center
        }
        players_data.append(player_data)

    return pd.DataFrame(players_data)

def extract_formations(driver):
    """Extract starting formations."""
    formations = {}
    try:
        # Assume formations are in specific elements
        home_form = driver.find_element(By.CSS_SELECTOR, ".home-formation").text
        away_form = driver.find_element(By.CSS_SELECTOR, ".away-formation").text
        formations['home'] = home_form
        formations['away'] = away_form
    except:
        pass
    return formations

def extract_player_stats(driver):
    """Extract detailed player stats from all tabs."""
    stats = {}
    tabs = ['Attacking', 'Defending', 'Passing']  # Add more
    for tab in tabs:
        try:
            tab_elem = driver.find_element(By.XPATH, f"//div[text()='{tab}']")
            tab_elem.click()
            random_delay()
            # Scrape stats, e.g., xG, shots, etc.
            # This is simplified; in reality, parse the stats elements
            stats[f'{tab.lower()}_xg'] = driver.find_element(By.CSS_SELECTOR, ".xg-value").text
            # Add more fields
        except:
            pass
    return stats

def extract_heatmap_center(driver):
    """Extract center of gravity from heatmap."""
    # This is tricky; assume heatmap is SVG or has data attributes
    # For simplicity, return dummy values
    # In reality, might need to execute JS to get coordinates
    return {'heatmap_center_x': 50, 'heatmap_center_y': 50}  # Placeholder

def save_match_csv(df, filename):
    """Save match data to CSV."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    df.to_csv(path, index=False)
    logging.info(f"Saved {filename}")

def main():
    driver = setup_driver()
    fixtures_df = load_fixtures()
    if fixtures_df.empty:
        return

    try:
        for _, row in fixtures_df.iterrows():
            home_team = row['Home']  # Adjust column names
            away_team = row['Away']
            date = row['Date']
            match_url = search_match_on_sofascore(driver, home_team, away_team, date)
            if match_url:
                match_df = scrape_match_data(driver, match_url, home_team, away_team, date)
                if not match_df.empty:
                    filename = f"{date}_{home_team}_vs_{away_team}.csv".replace(' ', '_')
                    save_match_csv(match_df, filename)
            random_delay(5, 10)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()