import pandas as pd
from sklearn.model_selection import train_test_split
import os
import logging

def calculate_fantasy_points(row):
    """Calculates a proxy for FPL points based on available FBREF stats."""
    points = 0
    if row['Min'] > 0: points += 1
    if row['Min'] >= 60: points += 1
        
    if row['Position'] == 'FWD': points += row['Gls'] * 4
    elif row['Position'] == 'MID': points += row['Gls'] * 5
    elif row['Position'] == 'DEF' or row['Position'] == 'GK': points += row['Gls'] * 6

    points += row['Ast'] * 3
    points -= row['CrdY'] * 1
    points -= row['CrdR'] * 3
    return points

def main():
    """Prepares the final, feature-rich dataset for modeling."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # --- Configuration ---
    PROCESSED_DATA_DIR = "processed_data"
    # --- CORRECTED FILENAME ---
    INPUT_FILE = "master_player_stats_v4_h2h_features.csv" 
    MODEL_DATA_DIR = "model_data_v4"
    
    input_path = os.path.join(PROCESSED_DATA_DIR, INPUT_FILE)

    # --- Load Data ---
    if not os.path.exists(input_path):
        logging.error(f"Error: Input file not found at {input_path}")
        return
    logging.info(f"Reading final feature-engineered data from {input_path}...")
    df = pd.read_csv(input_path)
    
    # --- 1. Define the Target Variable ---
    df = df[df['Min'] > 90].copy()
    df['FantasyPoints'] = df.apply(calculate_fantasy_points, axis=1)
    logging.info("Calculated 'FantasyPoints' target variable.")

    # --- 2. Feature Selection (Now including our new features) ---
    features = [
        # Original Player Features
        'xG_p90', 'xAG_p90', 'Gls_minus_xG', 'Ast_minus_xAG',
        'Starts', 'Min', '90s', 'CrdY', 'CrdR',
        # NEW H2H Features from v4 file
        'h2h_home_win_pct_home', 'h2h_avg_goals_home', 
        'h2h_home_win_pct_away', 'h2h_avg_goals_away',
        # Categorical Features
        'Squad', 'Position' 
    ]
    target = 'FantasyPoints'
    
    existing_features = [f for f in features if f in df.columns]
    logging.info(f"Selected {len(existing_features)} features for the v4 model.")
    model_df = df[existing_features + [target]].copy()
    
    # --- 3. One-Hot Encoding ---
    categorical_features = ['Squad', 'Position']
    model_df = pd.get_dummies(model_df, columns=categorical_features, drop_first=True)
    logging.info("Applied one-hot encoding to categorical features.")

    # --- 4. Train-Test Split ---
    X = model_df.drop(target, axis=1)
    y = model_df[target]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    logging.info("Split data into 80% training and 20% testing sets.")

    # --- Save the results to a new directory ---
    os.makedirs(MODEL_DATA_DIR, exist_ok=True)
    
    X_train.to_csv(os.path.join(MODEL_DATA_DIR, "X_train.csv"), index=False)
    X_test.to_csv(os.path.join(MODEL_DATA_DIR, "X_test.csv"), index=False)
    y_train.to_csv(os.path.join(MODEL_DATA_DIR, "y_train.csv"), index=False)
    y_test.to_csv(os.path.join(MODEL_DATA_DIR, "y_test.csv"), index=False)
    
    logging.info(f"\n--- v4 Model Preparation Complete ---")
    logging.info(f"Prepared data saved to the '{MODEL_DATA_DIR}' directory.")

if __name__ == '__main__':
    main()

