import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import joblib
import os
import logging
import sys

def main():
    """Main function to train and evaluate the v4 predictive model."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # --- Configuration ---
    MODEL_DATA_DIR = "model_data_v4" # Using the new v4 data directory
    MODEL_OUTPUT_DIR = "trained_models"
    MODEL_NAME = "fpl_oracle_model_v4.joblib" # Saving a new version of the model
    
    # --- Load Prepared Data ---
    logging.info("--- Loading Prepared v4 Data ---")
    try:
        X_train = pd.read_csv(os.path.join(MODEL_DATA_DIR, "X_train.csv"))
        y_train = pd.read_csv(os.path.join(MODEL_DATA_DIR, "y_train.csv")).values.ravel()
        X_test = pd.read_csv(os.path.join(MODEL_DATA_DIR, "X_test.csv"))
        y_test = pd.read_csv(os.path.join(MODEL_DATA_DIR, "y_test.csv")).values.ravel()
    except FileNotFoundError as e:
        logging.error(f"Error: Data files not found in {MODEL_DATA_DIR}. Please run the v4 preparation script first.")
        sys.exit(1)
        
    logging.info("v4 Data loaded successfully.")

    # --- Initialize and Train the Model ---
    logging.info("\n--- Training the v4 Oracle ---")
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    
    logging.info("Model: RandomForestRegressor")
    logging.info("Training started...")
    model.fit(X_train, y_train)
    logging.info("Training complete.")

    # --- Evaluate the Model ---
    logging.info("\n--- Evaluating v4 Model Performance ---")
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    
    logging.info(f"v4 Model Mean Absolute Error (MAE): {mae:.2f}")
    logging.info(f"This means, on average, our new model's prediction is +/- {mae:.2f} points from the actual score.")
    
    # --- Save the Trained Model ---
    logging.info("\n--- Saving the v4 Trained Model ---")
    os.makedirs(MODEL_OUTPUT_DIR, exist_ok=True)
    model_path = os.path.join(MODEL_OUTPUT_DIR, MODEL_NAME)
    joblib.dump(model, model_path)
    
    logging.info(f"v4 Model 'brain' saved to: {model_path}")
    logging.info("\n--- FPL Oracle v4.0 is Trained and Ready ---")

if __name__ == '__main__':
    main()