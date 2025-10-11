import soccerdata as sd
import pandas as pd
import os
import logging

def main():
    """
    Uses the soccerdata library to efficiently fetch detailed per-match player 
    statistics from SofaScore for the 2024-2025 Premier League season.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # --- Configuration ---
    LEAGUE = "ENG-Premier League"
    SEASON = "24-25"
    OUTPUT_DIR = "processed_data"
    OUTPUT_FILE = "sofascore_per_match_stats.csv"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    try:
        # --- 1. Initialize the SofaScore Scraper from the library ---
        logging.info(f"Initializing SofaScore data client for {LEAGUE} season {SEASON}...")
        # Caching is enabled by default, which is great for development.
        # It will only download data it doesn't already have.
        sofascore = sd.SofaScore(leagues=LEAGUE, seasons=SEASON)
        logging.info("Client initialized.")

        # --- 2. Fetch the Match-Level Player Statistics ---
        # The library handles all the complex scraping in the background.
        logging.info("Fetching detailed per-match player stats... This may take a while on the first run.")
        player_match_stats = sofascore.read_player_match_stats()
        logging.info(f"Successfully fetched stats for {len(player_match_stats)} player-match entries.")

        # --- 3. Save the Data ---
        # The data comes back as a clean pandas DataFrame.
        output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
        player_match_stats.to_csv(output_path, index=False)
        
        logging.info("\n--- SofaScore Data Acquisition Complete ---")
        logging.info(f"Complete per-match dataset saved to: {output_path}")

    except Exception as e:
        logging.error(f"An error occurred while using the soccerdata library: {e}")
        logging.error("Please ensure you have run 'pip install soccerdata' and that the library is up to date.")

if __name__ == '__main__':
    main()