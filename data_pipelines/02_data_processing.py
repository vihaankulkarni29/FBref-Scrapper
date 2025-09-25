import os
import pandas as pd
import glob
from pathlib import Path
from typing import Optional

def normalize_player_names(name: str) -> str:
    """
    A simple function to standardize player names.
    Can be expanded with more complex rules later.
    """
    # Example rule: FBREF sometimes uses backslashes for special characters
    return name.split('\\')[0].strip()


def find_player_column(df: pd.DataFrame) -> Optional[str]:
    """
    Finds the player column name in the DataFrame.
    Returns the first column containing 'Player', or None if not found.
    """
    possible_cols = [col for col in df.columns if 'Player' in col]
    return possible_cols[0] if possible_cols else None


def clean_column_headers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans column headers by taking the last part after '_'.
    Modifies the DataFrame in place and returns it.
    """
    cleaned_columns = {col: col.split('_')[-1] for col in df.columns}
    return df.rename(columns=cleaned_columns)


def merge_dataframes(dfs: list[pd.DataFrame], key: str) -> pd.DataFrame:
    """
    Merges a list of DataFrames on the given key using outer join.
    Drops duplicate columns from subsequent DataFrames except the key.
    """
    if not dfs:
        return pd.DataFrame()
    merged = dfs[0]
    for df in dfs[1:]:
        cols_to_drop = [col for col in df.columns if col in merged.columns and col != key]
        df = df.drop(columns=cols_to_drop, errors='ignore')
        merged = pd.merge(merged, df, on=key, how='outer')
    return merged


def process_season_data(season_dir: str) -> pd.DataFrame:
    """
    Loads all CSVs for a single season, merges them on player name, cleans headers, and returns the DataFrame.
    """
    season_path = Path(season_dir)
    if not season_path.is_dir():
        print(f"Season directory {season_dir} does not exist or is not a directory")
        return pd.DataFrame()

    csv_files = list(season_path.glob('*.csv'))
    if not csv_files:
        print(f"No CSV files found in {season_dir}")
        return pd.DataFrame()

    # Read the first file to determine the player column
    try:
        first_df = pd.read_csv(csv_files[0])
    except Exception as e:
        print(f"Could not read {csv_files[0]}. Error: {e}. Aborting season processing.")
        return pd.DataFrame()

    player_col = find_player_column(first_df)
    if not player_col:
        print(f"Could not determine a player column in {csv_files[0]}. Aborting season processing.")
        return pd.DataFrame()

    # Collect valid DataFrames
    dfs = []
    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            print(f"Could not read {file_path}. Error: {e}. Skipping.")
            continue

        if player_col not in df.columns:
            print(f"Warning: Player column '{player_col}' not found in {file_path}. Skipping this file for merge.")
            continue

        df[player_col] = df[player_col].apply(normalize_player_names)
        dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    # Merge the DataFrames
    merged_df = merge_dataframes(dfs, player_col)

    # Clean column headers
    merged_df = clean_column_headers(merged_df)

    return merged_df


def main():
    """Main execution function for the processing pipeline."""
    # --- Configuration ---
    RAW_DATA_DIR = "raw_data"
    PROCESSED_DATA_DIR = "processed_data"
    OUTPUT_FILE = "master_player_stats_v2.csv" # New output file name for the cleaned version

    # --- Execution ---
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    
    all_seasons_dfs = []
    season_dirs = [d for d in os.listdir(RAW_DATA_DIR) if os.path.isdir(os.path.join(RAW_DATA_DIR, d))]

    for season_name in season_dirs:
        print(f"\n--- Processing Season: {season_name} ---")
        season_dir_path = os.path.join(RAW_DATA_DIR, season_name)
        season_df = process_season_data(season_dir_path)
        if season_df is not None and not season_df.empty:
            season_df['Season'] = season_name # Add a column to identify the season
            all_seasons_dfs.append(season_df)
            print(f"Successfully processed {len(season_df.columns)} columns for {len(season_df)} players.")

    if all_seasons_dfs:
        master_df = pd.concat(all_seasons_dfs, ignore_index=True)
        # Drop columns that are entirely empty, which can happen with bad merges
        master_df.dropna(axis=1, how='all', inplace=True)
        # Drop duplicate columns that might arise from cleaning (e.g., 'Matches')
        master_df = master_df.loc[:,~master_df.columns.duplicated()]
        
        output_path = os.path.join(PROCESSED_DATA_DIR, OUTPUT_FILE)
        master_df.to_csv(output_path, index=False)
        print(f"\n--- Processing Complete ---")
        print(f"Master dataset created with {len(master_df)} total player entries.")
        print(f"File saved to: {output_path}")
    else:
        print("No data was processed.")


if __name__ == "__main__":
    main()