import pandas as pd
import os
import logging

def find_player_column(df):
    """Dynamically finds the player column in a dataframe."""
    # Prioritize the simple 'Player' column name which our new scraper produces
    if 'Player' in df.columns:
        return 'Player'
    # Fallback for older, messier formats
    possible_cols = [col for col in df.columns if 'Player' in col]
    if possible_cols:
        return possible_cols[0]
    return None

def process_season_data(season_path, season_name):
    """Loads, merges, and cleans all stat files for a single season using a composite key."""
    all_files = [f for f in os.listdir(season_path) if f.endswith('.csv')]
    if not all_files:
        logging.warning(f"No CSV files found in {season_path}. Skipping.")
        return None

    # --- COMPOSITE KEY UPGRADE ---
    # These columns are present in all tables and form a reliable unique ID
    merge_keys = ['Player', 'Nation', 'Pos', 'Squad', 'Age']
    
    merged_df = None

    for i, filename in enumerate(all_files):
        filepath = os.path.join(season_path, filename)
        try:
            df = pd.read_csv(filepath)
            
            # Basic validation to ensure the file has the necessary columns
            if not all(key in df.columns for key in merge_keys):
                logging.warning(f"File {filename} is missing one of the merge keys. Skipping.")
                continue

            if i == 0:
                merged_df = df
            else:
                # Drop duplicate informational columns from the right-side table before merging
                cols_to_drop = [col for col in df.columns if col in merged_df.columns and col not in merge_keys]
                df = df.drop(columns=cols_to_drop)
                merged_df = pd.merge(merged_df, df, on=merge_keys, how='outer')
        except Exception as e:
            logging.error(f"Failed to process file {filepath}: {e}")
            continue
    
    if merged_df is not None:
        merged_df['Season'] = season_name
        logging.info(f"Successfully processed {len(merged_df.columns)} columns for {len(merged_df)} players.")
    
    return merged_df

def main():
    """Main execution function."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    INPUT_DIR = "raw_data"
    OUTPUT_DIR = "processed_data"
    OUTPUT_FILE = "master_player_stats_v2.csv"
    
    SEASONS_TO_PROCESS = ["2023-2024", "2024-2025", "2025-2026"]
    
    all_seasons_dfs = []

    for season_name in SEASONS_TO_PROCESS:
        logging.info(f"\n--- Processing Season: {season_name} ---")
        season_path = os.path.join(INPUT_DIR, season_name)
        
        if not os.path.exists(season_path):
            logging.warning(f"Season directory not found: {season_path}. Skipping.")
            continue
            
        season_df = process_season_data(season_path, season_name)
        if season_df is not None:
            all_seasons_dfs.append(season_df)

    if not all_seasons_dfs:
        logging.error("No season data could be processed. Master file not created.")
        return

    master_df = pd.concat(all_seasons_dfs, ignore_index=True)
    
    # Drop any fully empty columns that might be created during merges
    master_df = master_df.dropna(axis=1, how='all')
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    
    try:
        master_df.to_csv(output_path, index=False)
        logging.info("\n--- Processing Complete ---")
        logging.info(f"Master dataset created with {len(master_df)} total player entries.")
        logging.info(f"File saved to: {output_path}")
    except PermissionError:
        logging.error(f"PERMISSION DENIED to write to {output_path}.")
        logging.error("Please ensure the file is not open in another program (like Excel) and try again.")

if __name__ == '__main__':
    main()

