import pandas as pd
import joblib
import os
import logging

def main():
    """
    Loads the trained v4 model and makes predictions on the latest player data.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # --- Configuration ---
    MODEL_DIR = "trained_models"
    MODEL_NAME = "fpl_oracle_model_v4.joblib"
    DATA_DIR = "processed_data"
    # --- CORRECTED FILENAME ---
    LATEST_DATA_FILE = "master_player_stats_v4_h2h_features.csv"
    TRAINING_DATA_COLUMNS_FILE = "model_data_v4/X_train.csv"
    PREDICTIONS_OUTPUT_DIR = "predictions"
    PREDICTIONS_FILE = "gameweek_predictions_v4.csv"

    # --- Load the Trained Model ---
    model_path = os.path.join(MODEL_DIR, MODEL_NAME)
    if not os.path.exists(model_path):
        logging.error(f"Error: Trained model not found at {model_path}. Please run the v4 training script first.")
        return
        
    logging.info(f"Loading trained v4 Oracle from {model_path}...")
    model = joblib.load(model_path)
    logging.info("Oracle v4.0 loaded successfully.")

    # --- Load the Latest Player Data to Predict On ---
    latest_data_path = os.path.join(DATA_DIR, LATEST_DATA_FILE)
    if not os.path.exists(latest_data_path):
        logging.error(f"Error: Latest data file not found at {latest_data_path}.")
        return
        
    logging.info(f"Loading latest player data from {latest_data_path}...")
    latest_df = pd.read_csv(latest_data_path)
    latest_season = latest_df['Season'].max()
    predict_df = latest_df[latest_df['Season'] == latest_season].copy()
    logging.info(f"Predicting for season: {latest_season}")
    
    player_info = predict_df[['Player', 'Squad']].copy()
    
    # --- Prepare the Data for Prediction (Critical Step) ---
    logging.info("Preparing data for prediction...")
    predict_df_encoded = pd.get_dummies(predict_df, columns=['Squad', 'Position'], drop_first=True)
    
    try:
        training_columns = pd.read_csv(TRAINING_DATA_COLUMNS_FILE).columns
    except FileNotFoundError:
        logging.error(f"Error: Training column template not found at {TRAINING_DATA_COLUMNS_FILE}")
        return

    for col in training_columns:
        if col not in predict_df_encoded.columns:
            predict_df_encoded[col] = 0
            
    predict_df_aligned = predict_df_encoded[training_columns]
    logging.info("Data aligned with model's training format.")

    # --- Make Predictions ---
    logging.info("\n--- Oracle v4.0 is now predicting FPL points... ---")
    predictions = model.predict(predict_df_aligned)
    
    # --- Create the Final Intelligence Report ---
    player_info['Predicted_Points'] = predictions
    final_report = player_info.sort_values(by='Predicted_Points', ascending=False).reset_index(drop=True)
    
    os.makedirs(PREDICTIONS_OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(PREDICTIONS_OUTPUT_DIR, PREDICTIONS_FILE)
    final_report.to_csv(output_path, index=False)
    
    logging.info(f"\n--- Prediction Complete ---")
    print("\nTop 20 Predicted Scorers (Oracle v4.0):")
    print(final_report.head(20).round(2))
    logging.info(f"\nFull report saved to: {output_path}")

if __name__ == '__main__':
    main()

