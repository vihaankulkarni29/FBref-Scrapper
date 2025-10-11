import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import logging
import functools

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
SEASONS = ["2023-2024", "2024-2025"]  # Add more seasons as needed
BASE_URL = "https://fbref.com/en/comps/9"
PLAYER_STATS_URL = f"{BASE_URL}/stats/Premier-League-Stats"
OUTPUT_DIR = "fbref_data"

def setup_driver():
    """Setup Selenium WebDriver with Ghost Protocol configuration."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def random_delay(min_delay=1, max_delay=3):
    """Add random delay to mimic human behavior."""
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

def get_season_url(season):
    """Get the URL for a specific season's player stats."""
    # For current season, use base URL. For historical, modify accordingly.
    # FBREF URLs for historical seasons: https://fbref.com/en/comps/9/2023-2024/stats/2023-2024-Premier-League-Stats
    return f"{BASE_URL}/{season}/stats/{season}-Premier-League-Stats"

@retry_on_failure()
def scrape_player_stats(driver, season):
    """Scrape all player stats tables for a season."""
    url = get_season_url(season)
    logging.info(f"Scraping player stats for {season} from {url}")
    driver.get(url)
    random_delay()

    tables_data = {}

    # Table IDs or classes on FBREF
    table_ids = {
        'Standard': 'stats_standard',
        'Shooting': 'stats_shooting',
        'Passing': 'stats_passing',
        'Goal and Shot Creation': 'stats_gca',
        'Defensive Actions': 'stats_defense',
        'Possession': 'stats_possession'
    }

    for table_name, table_id in table_ids.items():
        try:
            # Some tables might be in tabs, need to click
            # For simplicity, assume direct access, but in reality, might need to handle tabs
            table_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, table_id))
            )
            table_html = table_element.get_attribute('outerHTML')
            df = pd.read_html(table_html)[0]
            tables_data[table_name] = clean_table(df)
            logging.info(f"Scraped {table_name} table")
        except Exception as e:
            logging.warning(f"Failed to scrape {table_name}: {e}")

    # Merge all tables on player name or something
    if tables_data:
        merged_df = merge_player_tables(tables_data)
        return merged_df
    return pd.DataFrame()

def clean_table(df):
    """Clean a single table: handle headers, remove junk rows."""
    # FBREF tables have multi-level headers
    if isinstance(df.columns, pd.MultiIndex):
        # Flatten multi-level headers
        df.columns = ['_'.join(col).strip() for col in df.columns.values]
    # Remove rows that are repeated headers
    df = df[~df.iloc[:, 0].str.contains('Rk|Player', na=False, case=False)]
    # Ensure numeric columns are numeric
    for col in df.columns:
        if col != 'Player':  # Assuming 'Player' is the name column
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def merge_player_tables(tables):
    """Merge all player stat tables into one."""
    base_df = tables['Standard']
    for name, df in tables.items():
        if name != 'Standard':
            # Merge on 'Player' column, assuming it exists
            base_df = base_df.merge(df, on='Player', how='left', suffixes=('', f'_{name.lower()}'))
    return base_df

@retry_on_failure()
def scrape_fixtures(driver, season):
    """Scrape fixtures for a season."""
    url = f"{BASE_URL}/{season}/schedule/{season}-Premier-League-Scores-and-Fixtures"
    logging.info(f"Scraping fixtures for {season} from {url}")
    driver.get(url)
    random_delay()

    try:
        table_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'sched_all'))  # Assuming the table ID
        )
        table_html = table_element.get_attribute('outerHTML')
        df = pd.read_html(table_html)[0]
        df = clean_fixtures_table(df)
        return df
    except Exception as e:
        logging.error(f"Failed to scrape fixtures: {e}")
        return pd.DataFrame()

def clean_fixtures_table(df):
    """Clean fixtures table."""
    # Similar cleaning as player tables
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ['_'.join(col).strip() for col in df.columns.values]
    # Remove junk rows
    df = df.dropna(subset=['Date'])  # Assuming 'Date' column exists
    return df

def save_to_csv(df, filename):
    """Save DataFrame to CSV."""
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    df.to_csv(path, index=False)
    logging.info(f"Saved {filename}")

def main():
    driver = setup_driver()
    try:
        for season in SEASONS:
            # Scrape player stats
            player_df = scrape_player_stats(driver, season)
            if not player_df.empty:
                save_to_csv(player_df, f"fbref_player_stats_{season}.csv")

            # Scrape fixtures
            fixtures_df = scrape_fixtures(driver, season)
            if not fixtures_df.empty:
                save_to_csv(fixtures_df, f"fbref_fixtures_{season}.csv")

            random_delay(5, 10)  # Longer delay between seasons
    finally:
        driver.quit()

if __name__ == "__main__":
    main()