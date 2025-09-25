import pandas as pd
import numpy as np
import os

def assign_position(pos_str: str) -> str:
    """Assigns a general position based on the detailed Pos string from FBREF."""
    if 'FW' in pos_str:
        return 'FWD'
    if 'MF' in pos_str:
        return 'MID'
    if 'DF' in pos_str:
        return 'DEF'
    return 'GK' # Assuming if none of the above, it's a Goalkeeper

def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes the cleaned master dataframe and engineers new predictive features.
    """
    # --- Convert relevant columns to numeric, coercing errors to NaN ---
    numeric_cols = ['Min', '90s', 'Gls', 'Ast', 'xG', 'npxG', 'xAG', 'SCA', 'GCA', 'Touches'] 
    # Find which of these columns actually exist in the dataframe to avoid KeyErrors
    cols_to_convert = [col for col in numeric_cols if col in df.columns]
    for col in cols_to_convert:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Fill any resulting NaNs in these columns with 0
    df[cols_to_convert] = df[cols_to_convert].fillna(0)

    # --- Feature Engineering ---
    
    # 1. Per 90 Metrics (handle division by zero)
    df['Min'] = df['Min'].replace(0, np.nan) # Avoid division by zero, temporarily
    df['90s'] = df['Min'] / 90
    df['90s'] = df['90s'].fillna(0) # Put zeros back

    if 'xG' in df.columns:
        df['xG_p90'] = (df['xG'] / df['90s']).fillna(0)
    if 'xAG' in df.columns:
        df['xAG_p90'] = (df['xAG'] / df['90s']).fillna(0)
    if 'SCA' in df.columns:
        df['SCA_p90'] = (df['SCA'] / df['90s']).fillna(0)
    if 'Touches' in df.columns: # Assuming a general 'Touches' column exists
        # In the future we would use 'Touches (Att Pen)' specifically if scraped
        df['Touches_p90'] = (df['Touches'] / df['90s']).fillna(0)

    # 2. Efficiency & Conversion Ratios
    if 'Gls' in df.columns and 'xG' in df.columns:
        df['Gls_minus_xG'] = df['Gls'] - df['xG']
    if 'Ast' in df.columns and 'xAG' in df.columns:
        df['Ast_minus_xAG'] = df['Ast'] - df['xAG']

    # 3. Positional Grouping
    if 'Pos' in df.columns:
        df['Position'] = df['Pos'].apply(assign_position)

    # Clean up infinite values that might result from division by zero
    df.replace([np.inf, -np.inf], 0, inplace=True)
    
    return df

def main():
    """Main execution function."""
    # --- Configuration ---
    PROCESSED_DATA_DIR = "processed_data"
    INPUT_FILE = "master_player_stats_v2.csv"
    OUTPUT_FILE = "master_player_stats_v3_features.csv"
    
    input_path = os.path.join(PROCESSED_DATA_DIR, INPUT_FILE)
    output_path = os.path.join(PROCESSED_DATA_DIR, OUTPUT_FILE)

    # --- Execution ---
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at {input_path}")
        return

    print(f"Reading cleaned data from {input_path}...")
    master_df = pd.read_csv(input_path)

    print("Engineering new features...")
    featured_df = create_features(master_df)

    featured_df.to_csv(output_path, index=False)
    print(f"\n--- Feature Engineering Complete ---")
    print(f"Enriched dataset created with {len(featured_df.columns)} columns.")
    print(f"File saved to: {output_path}")

if __name__ == '__main__':
    main()
