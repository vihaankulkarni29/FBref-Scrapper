import pandas as pd
import joblib
import os
import logging

def main():
    """
    Loads the trained model and makes predictions on the latest player data for the experiment.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # --- Configuration ---
    MODEL_DIR = "trained_models"
    # We will use the model we trained for the experiment
    MODEL_NAME = "fpl_oracle_model_experiment.joblib" 
    DATA_DIR = "processed_data"
    LATEST_DATA_FILE = "master_player_stats_v3_features.csv"
    TRAINING_DATA_COLUMNS_FILE = "model_data_experiment/X_train.csv" # Align with the experiment data
    PREDICTIONS_OUTPUT_DIR = "predictions"
    PREDICTIONS_FILE = "gameweek_predictions_experiment.csv"

    # --- Load the Trained Model ---
    model_path = os.path.join(MODEL_DIR, MODEL_NAME)
    if not os.path.exists(model_path):
        logging.error(f"Error: Trained experiment model not found at {model_path}. Please run the experiment training script first.")
        return
        
    logging.info(f"Loading trained Oracle from {model_path}...")
    model = joblib.load(model_path)
    logging.info("Oracle loaded successfully.")

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
    
    # --- Prepare the Data for Prediction ---
    logging.info("Preparing data for prediction...")
    predict_df_encoded = pd.get_dummies(predict_df, columns=['Squad', 'Position'], drop_first=True)
    
    try:
        training_columns = pd.read_csv(TRAINING_DATA_COLUMNS_FILE).columns
    except FileNotFoundError:
        logging.error(f"Error: Training column template not found at {TRAINING_DATA_COLUMNS_FILE}")
        return

    # Add any missing one-hot encoded columns and fill with 0
    for col in training_columns:
        if col not in predict_df_encoded.columns:
            predict_df_encoded[col] = 0
            
    # Ensure the order of columns is the same as the training data
    predict_df_aligned = predict_df_encoded[training_columns]
    
    # --- PRE-PREDICTION SANITIZATION (CRITICAL FIX) ---
    # Convert all feature columns to numeric, coercing errors
    for col in predict_df_aligned.columns:
        predict_df_aligned[col] = pd.to_numeric(predict_df_aligned[col], errors='coerce')
    
    # Fill any values that couldn't be converted with 0
    predict_df_aligned = predict_df_aligned.fillna(0)
    logging.info("Sanitized all feature columns to be numeric.")

    # --- Make Predictions ---
    logging.info("\n--- Oracle is now predicting FPL points... ---")
    predictions = model.predict(predict_df_aligned)
    
    # --- Create the Final Intelligence Report ---
    player_info['Predicted_Points'] = predictions
    final_report = player_info.sort_values(by='Predicted_Points', ascending=False).reset_index(drop=True)
    
    os.makedirs(PREDICTIONS_OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(PREDICTIONS_OUTPUT_DIR, PREDICTIONS_FILE)
    final_report.to_csv(output_path, index=False)
    
    logging.info(f"\n--- Prediction Complete ---")
    print("\nTop 20 Predicted Scorers (Experiment):")
    print(final_report.head(20).round(2))
    logging.info(f"\nFull report saved to: {output_path}")

if __name__ == '__main__':
    main()
