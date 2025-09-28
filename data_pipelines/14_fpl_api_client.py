import requests
import pandas as pd
import os
import logging

def main():
    """
    Connects to the official FPL API to download master player data and
    detailed gameweek histories for the last two seasons.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # --- Configuration ---
    BASE_URL = "https://fantasy.premierleague.com/api/"
    OUTPUT_DIR = "processed_data" # We save directly to processed as this data is clean
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # --- 1. Fetch the Master Bootstrap Data ---
    # This contains the player directory, teams, positions, etc.
    try:
        logging.info("Fetching master bootstrap data from FPL API...")
        bootstrap_data = requests.get(f"{BASE_URL}bootstrap-static/").json()
        logging.info("Successfully fetched bootstrap data.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch bootstrap data: {e}")
        return

    # --- 2. Create the Player Directory ---
    players = bootstrap_data['elements']
    teams = {team['id']: team['name'] for team in bootstrap_data['teams']}
    positions = {pos['id']: pos['singular_name_short'] for pos in bootstrap_data['element_types']}

    player_directory_data = []
    for p in players:
        player_directory_data.append({
            'player_id': p['id'],
            'first_name': p['first_name'],
            'second_name': p['second_name'],
            'team_name': teams.get(p['team_code'], 'Unknown'),
            'position': positions.get(p['element_type'], 'Unknown'),
            'current_price': p['now_cost'] / 10.0 # Price is in tenths of a million
        })
    
    player_directory_df = pd.DataFrame(player_directory_data)
    player_directory_output_path = os.path.join(OUTPUT_DIR, "fpl_player_directory.csv")
    player_directory_df.to_csv(player_directory_output_path, index=False)
    logging.info(f"Player directory created with {len(player_directory_df)} players.")
    logging.info(f"File saved to: {player_directory_output_path}")

    # --- 3. Fetch Detailed Gameweek History for Each Player ---
    logging.info("\nFetching detailed gameweek history for all players...")
    all_gameweek_data = []
    player_ids = player_directory_df['player_id'].tolist()

    for i, player_id in enumerate(player_ids):
        try:
            player_detail_url = f"{BASE_URL}element-summary/{player_id}/"
            player_detail_data = requests.get(player_detail_url).json()
            
            # We are interested in the 'history' key which contains past season gameweek data
            for gw in player_detail_data.get('history', []):
                gw['player_id'] = player_id # Add player_id to link the data
                all_gameweek_data.append(gw)

            if (i + 1) % 50 == 0:
                logging.info(f"Processed {i + 1}/{len(player_ids)} players...")

        except requests.exceptions.RequestException as e:
            logging.warning(f"Could not fetch data for player_id {player_id}: {e}")
            continue
    
    if not all_gameweek_data:
        logging.error("No gameweek history could be fetched. Aborting.")
        return

    gameweek_history_df = pd.DataFrame(all_gameweek_data)
    gameweek_history_output_path = os.path.join(OUTPUT_DIR, "fpl_gameweek_history.csv")
    gameweek_history_df.to_csv(gameweek_history_output_path, index=False)
    logging.info(f"\n--- FPL API Data Acquisition Complete ---")
    logging.info(f"Gameweek history created with {len(gameweek_history_df)} entries.")
    logging.info(f"File saved to: {gameweek_history_output_path}")


if __name__ == '__main__':
    main()