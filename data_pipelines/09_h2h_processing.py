import pandas as pd
import os
import logging

def main():
    """
    Reads all raw H2H files, cleans them, de-duplicates matches, 
    and creates a single master H2H file.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # --- Configuration ---
    INPUT_DIR = "raw_data/h2h"
    OUTPUT_DIR = "processed_data"
    OUTPUT_FILE = "h2h_master.csv"

    if not os.path.exists(INPUT_DIR):
        logging.error(f"Input directory not found: {INPUT_DIR}. Please run the H2H scraper first.")
        return

    all_matches = []
    
    # --- 1. Read and Combine All Raw Files ---
    raw_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.csv')]
    if not raw_files:
        logging.error(f"No raw H2H files found in {INPUT_DIR}.")
        return

    logging.info(f"Found {len(raw_files)} raw H2H files to process.")

    for filename in raw_files:
        try:
            # Extract team name and season from filename
            parts = filename.replace('_h2h.csv', '').split('_')
            season = parts[-1]
            team_name = ' '.join(parts[:-1])
            
            filepath = os.path.join(INPUT_DIR, filename)
            df = pd.read_csv(filepath)
            
            # Add perspective team and season
            df['Team'] = team_name
            df['Season'] = season
            all_matches.append(df)
        except Exception as e:
            logging.error(f"Failed to process file {filename}: {e}")

    if not all_matches:
        logging.warning("No valid H2H files were loaded. Exiting early to avoid downstream errors.")
        return
    else:
        master_df = pd.concat(all_matches, ignore_index=True)
        logging.info(f"Combined all files into a single DataFrame with {len(master_df)} total rows.")

    # --- 2. Deep Cleaning ---
    # Remove rows that are just repeated headers
    master_df = master_df[master_df['Date'] != 'Date'].copy()
    master_df = master_df.dropna(subset=['Date', 'Opponent']) # Drop any other invalid rows
    
    # Standardize result (W, L, D)
    master_df['Result'] = master_df['Result'].str[0]

    # --- 3. De-duplicate Matches (Critical Step) ---
    # Create a unique, sorted key for each match to identify duplicates
    # e.g., Liverpool vs West Ham and West Ham vs Liverpool get the same key
    master_df['match_key'] = master_df.apply(
        lambda row: '_'.join(sorted([row['Team'], row['Opponent']])) + '_' + row['Date'], 
        axis=1
    )
    
    # Keep only the first occurrence of each unique match
    original_rows = len(master_df)
    deduplicated_df = master_df.drop_duplicates(subset=['match_key'], keep='first')
    final_rows = len(deduplicated_df)
    logging.info(f"De-duplication complete. Removed {original_rows - final_rows} duplicate match entries.")

    # --- 4. Final Touches & Save ---
    # Clean up and select final columns
    final_df = deduplicated_df.drop(columns=['match_key'])
    final_df = final_df.sort_values(by=['Season', 'Date']).reset_index(drop=True)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    final_df.to_csv(output_path, index=False)
    
    logging.info("\n--- H2H Processing Complete ---")
    logging.info(f"Final master H2H file has {len(final_df)} unique matches.")
    logging.info(f"Master file saved to: {output_path}")

if __name__ == '__main__':
    main()
    