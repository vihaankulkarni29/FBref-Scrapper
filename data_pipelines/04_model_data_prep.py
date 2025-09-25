import pandas as pd
from sklearn.model_selection import train_test_split
import os

def calculate_fantasy_points(row):
    """
    Calculates a proxy for FPL points based on available FBREF stats.
    This is a simplified model and can be expanded.
    """
    points = 0
    
    # Points for playing
    if row['Min'] > 0:
        points += 1
    if row['Min'] >= 60:
        points += 1 # An additional point for 60+ minutes
        
    # Points for goals, varying by position
    if row['Position'] == 'FWD':
        points += row['Gls'] * 4
    elif row['Position'] == 'MID':
        points += row['Gls'] * 5
    elif row['Position'] == 'DEF':
        points += row['Gls'] * 6
    else: # Goalkeepers
        points += row['Gls'] * 6

    # Points for assists
    points += row['Ast'] * 3
    
    # Negative points for cards
    points -= row['CrdY'] * 1
    points -= row['CrdR'] * 3
    
    # Note: Clean sheets, bonus points, saves, etc., are not included
    # as they are not directly available in this FBREF dataset.
    
    return points

def main():
    """Main execution function for preparing data for modeling."""
    
    # --- Configuration ---
    PROCESSED_DATA_DIR = "processed_data"
    INPUT_FILE = "master_player_stats_v3_features.csv"
    
    input_path = os.path.join(PROCESSED_DATA_DIR, INPUT_FILE)

    # --- Load Data ---
    if not os.path.exists(input_path):
        print(f"Error: Input file not found at {input_path}")
        return
    print(f"Reading feature-engineered data from {input_path}...")
    df = pd.read_csv(input_path)
    
    # --- 1. Define the Target Variable ---
    # Drop players with very few minutes as they add noise
    df = df[df['Min'] > 90].copy()
    print(f"Filtered down to {len(df)} players with more than 90 minutes played.")
    
    df['FantasyPoints'] = df.apply(calculate_fantasy_points, axis=1)
    print("Calculated 'FantasyPoints' target variable.")

    # --- 2. Feature Selection ---
    features = [
        # Engineered Features
        'xG_p90', 'xAG_p90', 'SCA_p90', 'Touches_p90', 
        'Gls_minus_xG', 'Ast_minus_xAG',
        # Core Stats
        'Starts', 'Min', '90s', 'CrdY', 'CrdR',
        # Categorical Features
        'Squad', 'Position' 
    ]
    
    target = 'FantasyPoints'
    
    # Keep only the columns we need
    # Make sure all selected features exist in the dataframe
    existing_features = [f for f in features if f in df.columns]
    print(f"Selected {len(existing_features)} features for the model.")
    
    model_df = df[existing_features + [target]].copy()
    
    # --- 3. One-Hot Encoding for Categorical Data ---
    categorical_features = ['Squad', 'Position']
    model_df = pd.get_dummies(model_df, columns=categorical_features, drop_first=True)
    print("Applied one-hot encoding to categorical features.")

    # --- 4. Train-Test Split ---
    X = model_df.drop(target, axis=1)
    y = model_df[target]
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print("Split data into 80% training and 20% testing sets.")

    # --- Save the results ---
    # Create a directory for the model-ready data
    MODEL_DATA_DIR = "model_data"
    os.makedirs(MODEL_DATA_DIR, exist_ok=True)
    
    X_train.to_csv(os.path.join(MODEL_DATA_DIR, "X_train.csv"), index=False)
    X_test.to_csv(os.path.join(MODEL_DATA_DIR, "X_test.csv"), index=False)
    y_train.to_csv(os.path.join(MODEL_DATA_DIR, "y_train.csv"), index=False)
    y_test.to_csv(os.path.join(MODEL_DATA_DIR, "y_test.csv"), index=False)
    
    print(f"\n--- Model Preparation Complete ---")
    print(f"Prepared data saved to the '{MODEL_DATA_DIR}' directory.")
    print(f"Training set has {len(X_train)} players.")
    print(f"Testing set has {len(X_test)} players.")


if __name__ == '__main__':
    main()