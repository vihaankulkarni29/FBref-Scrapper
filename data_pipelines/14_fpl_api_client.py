import requests
import pandas as pd
import os
import logging
import time
import random
import json

def fetch_fpl_data(url, max_retries=3, timeout=10):
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 429:
                if attempt == max_retries:
                    logging.error(f"429 Too Many Requests for {url}, retries exhausted")
                    response.raise_for_status()
                retry_after = response.headers.get('Retry-After')
                if retry_after:
                    try:
                        sleep_time = int(retry_after)
                    except ValueError:
                        sleep_time = 60
                else:
                    sleep_time = 2 ** attempt
                logging.warning(f"429 Too Many Requests for {url}, retrying in {sleep_time}s (attempt {attempt+1}/{max_retries+1})")
                time.sleep(sleep_time)
                continue
            response.raise_for_status()
            try:
                return response.json()
            except json.JSONDecodeError as e:
                logging.error(f"JSON decode error for {url}: {e}")
                raise
        except requests.exceptions.RequestException as e:
            logging.error(f"Request error for {url}: {e}")
            raise

def main():
    """
    Connects to the official FPL API to download master player data and
    detailed gameweek histories for the last two seasons with corrected team mapping.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # --- Configuration ---
    BASE_URL = "https://fantasy.premierleague.com/api/"
    OUTPUT_DIR = "processed_data"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- 1. Fetch the Master Bootstrap Data ---
    try:
        logging.info("Fetching master bootstrap data from FPL API...")
        bootstrap_data = fetch_fpl_data(f"{BASE_URL}bootstrap-static/")
        logging.info("Successfully fetched bootstrap data.")
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        logging.error(f"Failed to fetch bootstrap data: {e}")
        return

    # --- 2. Create Corrected Mappings and Player Directory ---
    players = bootstrap_data.get('elements', [])
    
    # --- UPGRADED MAPPING LOGIC ---
    # We will now use the more stable 'code' for teams instead of 'id'.
    teams = {team['code']: team['name'] for team in bootstrap_data.get('teams', [])}
    positions = {pos['id']: pos['singular_name_short'] for pos in bootstrap_data.get('element_types', [])}

    player_directory_data = []
    for p in players:
        player_directory_data.append({
            'player_id': p['id'],
            'first_name': p['first_name'],
            'second_name': p['second_name'],
            'full_name': f"{p['first_name']} {p['second_name']}",
            # Use the player's 'team_code' to look up in our new 'teams' dictionary
            'team_name': teams.get(p['team_code'], 'Unknown'), 
            'position': positions.get(p['element_type'], 'Unknown'),
            'current_price': p['now_cost'] / 10.0
        })
    
    player_directory_df = pd.DataFrame(player_directory_data)
    player_directory_output_path = os.path.join(OUTPUT_DIR, "fpl_player_directory.csv")
    try:
        player_directory_df.to_csv(player_directory_output_path, index=False)
        logging.info(f"Corrected player directory created with {len(player_directory_df)} players.")
        logging.info(f"File saved to: {player_directory_output_path}")
    except Exception as e:
        logging.error(f"Failed to save player directory CSV: {e}")
        return

    # --- 3. Fetch Detailed Gameweek History (No changes needed here) ---
    logging.info("\nFetching detailed gameweek history for all players...")
    all_gameweek_data = []
    player_ids = player_directory_df['player_id'].tolist()

    for i, player_id in enumerate(player_ids):
        try:
            player_detail_url = f"{BASE_URL}element-summary/{player_id}/"
            time.sleep(random.uniform(0.1, 0.3))
            player_detail_data = fetch_fpl_data(player_detail_url)

            for gw in player_detail_data.get('history', []):
                gw['player_id'] = player_id
                all_gameweek_data.append(gw)

            if (i + 1) % 50 == 0:
                logging.info(f"Processed {i + 1}/{len(player_ids)} players...")

        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            logging.warning(f"Could not fetch data for player_id {player_id}: {e}")
            continue
    
    if not all_gameweek_data:
        logging.error("No gameweek history could be fetched. Aborting.")
        return

    gameweek_history_df = pd.DataFrame(all_gameweek_data)
    gameweek_history_output_path = os.path.join(OUTPUT_DIR, "fpl_gameweek_history.csv")
    try:
        gameweek_history_df.to_csv(gameweek_history_output_path, index=False)
        logging.info(f"\n--- FPL API Data Acquisition Complete ---")
        logging.info(f"Gameweek history created with {len(gameweek_history_df)} entries.")
        logging.info(f"File saved to: {gameweek_history_output_path}")
    except Exception as e:
        logging.error(f"Failed to save gameweek history CSV: {e}")

if __name__ == '__main__':
    main()

