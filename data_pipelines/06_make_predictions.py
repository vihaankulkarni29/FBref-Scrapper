import pandas as pd
import joblib
import os
from pathlib import Path

def main():
    """
    Main function to load the trained model and make predictions on the latest player data.
    """
    
    # --- Configuration ---
    repo_root = Path(__file__).resolve().parent.parent
    MODEL_DIR = repo_root / "trained_models"
    MODEL_NAME = "fpl_oracle_model.joblib"
    LATEST_DATA_FILE = repo_root / "processed_data" / "master_player_stats_v3_features.csv"
    TRAINING_DATA_COLUMNS_FILE = repo_root / "model_data" / "X_train.csv"  # To get the column structure
    PREDICTIONS_OUTPUT_DIR = repo_root / "predictions"
    PREDICTIONS_FILE = PREDICTIONS_OUTPUT_DIR / "gameweek_predictions.csv"

    # --- Load the Trained Model ---
    model_path = MODEL_DIR / MODEL_NAME
    if not os.path.exists(model_path):
        print(f"Error: Trained model not found at {model_path}. Please run the training script first.")
        return
        
    print(f"Loading trained Oracle from {model_path}...")
    model = joblib.load(model_path)
    print("Oracle loaded successfully.")

    # --- Load the Latest Player Data to Predict On ---
    latest_data_path = LATEST_DATA_FILE
    if not os.path.exists(latest_data_path):
        print(f"Error: Latest data file not found at {latest_data_path}.")
        return
        
    print(f"Loading latest player data from {latest_data_path}...")
    latest_df = pd.read_csv(latest_data_path)
    # Filter for the most recent season available in the data
    latest_season = latest_df['Season'].max()
    predict_df = latest_df[latest_df['Season'] == latest_season].copy()
    print(f"Predicting for season: {latest_season}")
    
    # Keep player names for the final report
    player_info = predict_df[['Player', 'Squad']].copy()
    
    # --- Prepare the Data for Prediction (Critical Step) ---
    print("Preparing data for prediction...")
    # 1. One-hot encode categorical features
    predict_df_encoded = pd.get_dummies(predict_df, columns=['Squad', 'Position'], drop_first=True)
    
    # 2. Align columns with the training data
    # Load the training data columns to ensure the structure is identical
    try:
        training_columns = pd.read_csv(TRAINING_DATA_COLUMNS_FILE).columns
    except FileNotFoundError:
        print(f"Error: Training column template file not found at {TRAINING_DATA_COLUMNS_FILE}")
        return

    # Add any missing columns to the prediction set and fill with 0
    for col in training_columns:
        if col not in predict_df_encoded.columns:
            predict_df_encoded[col] = 0
            
    # Ensure the order of columns is the same as the training data
    predict_df_aligned = predict_df_encoded[training_columns]
    print("Data aligned with model's training format.")

    # --- Make Predictions ---
    print("\n--- Oracle is now predicting FPL points... ---")
    predictions = model.predict(predict_df_aligned)
    
    # --- Create the Final Intelligence Report ---
    player_info['Predicted_Points'] = predictions
    
    # Sort by the highest predicted points
    final_report = player_info.sort_values(by='Predicted_Points', ascending=False).reset_index(drop=True)
    
    # Save the report to a CSV
    os.makedirs(PREDICTIONS_OUTPUT_DIR, exist_ok=True)
    output_path = PREDICTIONS_FILE
    final_report.to_csv(output_path, index=False)
    
    print(f"\n--- Prediction Complete ---")
    print("Top 20 Predicted Scorers:")
    print(final_report.head(20))
    print(f"\nFull report saved to: {output_path}")


if __name__ == '__main__':
    main()