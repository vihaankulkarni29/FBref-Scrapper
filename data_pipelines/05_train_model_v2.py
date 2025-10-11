import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import joblib
import os
import logging

def main():
    """Main function to train and evaluate the predictive model for our experiment."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # --- Configuration for the Experiment ---
    # Pointing to the correct input directory
    MODEL_DATA_DIR = "model_data_experiment" 
    MODEL_OUTPUT_DIR = "trained_models"
    # Saving the model with a specific name for the experiment
    MODEL_NAME = "fpl_oracle_model_experiment.joblib" 
    
    # --- Load Prepared Data ---
    logging.info(f"--- Loading Experiment Data from {MODEL_DATA_DIR} ---")
    try:
        X_train = pd.read_csv(os.path.join(MODEL_DATA_DIR, "X_train.csv"))
        y_train = pd.read_csv(os.path.join(MODEL_DATA_DIR, "y_train.csv")).values.ravel()
        X_test = pd.read_csv(os.path.join(MODEL_DATA_DIR, "X_test.csv"))
        y_test = pd.read_csv(os.path.join(MODEL_DATA_DIR, "y_test.csv")).values.ravel()
    except FileNotFoundError as e:
        logging.error(f"Error: Data files not found in {MODEL_DATA_DIR}. Please run the experiment preparation script first.")
        return
        
    logging.info("Experiment data loaded successfully.")

    # --- Initialize and Train the Model ---
    logging.info("\n--- Training the Experiment Oracle ---")
    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    
    logging.info("Model: RandomForestRegressor")
    logging.info("Training started...")
    model.fit(X_train, y_train)
    logging.info("Training complete.")

    # --- Evaluate the Model ---
    logging.info("\n--- Evaluating Experiment Model Performance ---")
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    
    logging.info(f"Experiment Model Mean Absolute Error (MAE): {mae:.2f}")
    logging.info(f"This means, on average, the prediction is +/- {mae:.2f} points from the actual score.")
    
    # --- Save the Trained Model ---
    logging.info("\n--- Saving the Experiment Model ---")
    os.makedirs(MODEL_OUTPUT_DIR, exist_ok=True)
    model_path = os.path.join(MODEL_OUTPUT_DIR, MODEL_NAME)
    joblib.dump(model, model_path)
    
    logging.info(f"Experiment model saved to: {model_path}")
    logging.info("\n--- FPL Experiment Oracle is Trained and Ready ---")

if __name__ == '__main__':
    main()
