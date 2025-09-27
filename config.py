import os
import platform
import shutil

# --- Team Configuration ---
# Dictionary mapping team names to their FBref squad IDs and URL-friendly slugs
TEAMS_CONFIG = {
    "Arsenal": {"id": "18bb7c10", "slug": "Arsenal"},
    "Aston Villa": {"id": "8602292d", "slug": "Aston-Villa"},
    "Bournemouth": {"id": "4ba7c610", "slug": "Bournemouth"},
    "Brentford": {"id": "cd051869", "slug": "Brentford"},
    "Brighton": {"id": "d07537b9", "slug": "Brighton-and-Hove-Albion"},
    "Chelsea": {"id": "cff3d9bb", "slug": "Chelsea"},
    "Crystal Palace": {"id": "47c64c55", "slug": "Crystal-Palace"},
    "Everton": {"id": "d3fd31cc", "slug": "Everton"},
    "Fulham": {"id": "fd962109", "slug": "Fulham"},
    "Ipswich Town": {"id": "c477b224", "slug": "Ipswich-Town"},
    "Leicester City": {"id": "a2d435b3", "slug": "Leicester-City"},
    "Liverpool": {"id": "822bd0ba", "slug": "Liverpool"},
    "Manchester City": {"id": "b8fd03ef", "slug": "Manchester-City"},
    "Manchester Utd": {"id": "19538871", "slug": "Manchester-United"},
    "Newcastle Utd": {"id": "b2b47a98", "slug": "Newcastle-United"},
    "Nott'ham Forest": {"id": "e4a775cb", "slug": "Nottingham-Forest"},
    "Southampton": {"id": "33c895d4", "slug": "Southampton"},
    "Tottenham": {"id": "361ca564", "slug": "Tottenham-Hotspur"},
    "West Ham": {"id": "7c21e445", "slug": "West-Ham-United"},
    "Wolves": {"id": "8cec06e1", "slug": "Wolverhampton-Wanderers"}
}

# --- Scraping Configuration ---
SEASONS_TO_SCRAPE = ["2023-2024", "2024-2025"]
MOST_RECENT_SEASON = "2024-2025"
OUTPUT_DIR = "raw_data/h2h"

# --- Selenium Configuration ---
MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds
# Determine Chrome binary path based on OS
chrome_binary_env = os.getenv('CHROME_BINARY')
if chrome_binary_env:
    CHROME_BINARY_PATH = chrome_binary_env
else:
    system = platform.system()
    if system == 'Windows':
        CHROME_BINARY_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    elif system == 'Darwin':  # macOS
        CHROME_BINARY_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    elif system == 'Linux':
        for name in ['google-chrome', 'chrome', 'chromium', 'chromium-browser']:
            path = shutil.which(name)
            if path:
                CHROME_BINARY_PATH = path
                break
        else:
            CHROME_BINARY_PATH = None
    else:
        CHROME_BINARY_PATH = None