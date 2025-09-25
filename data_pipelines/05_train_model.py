import argparse
import logging
import os
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error


def setup_logging(log_level: str = "INFO") -> None:
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def load_data(model_data_dir: Path) -> Tuple[pd.DataFrame, np.ndarray, pd.DataFrame, np.ndarray]:
    """
    Load training and testing data from CSV files.

    Args:
        model_data_dir: Directory containing the data files.s

    Returns:
        Tuple of (X_train, y_train, X_test, y_test).

    Raises:
        FileNotFoundError: If any required data file is missing.
        ValueError: If data loading fails.
    """
    try:
        X_train = pd.read_csv(model_data_dir / "X_train.csv")
        y_train = pd.read_csv(model_data_dir / "y_train.csv").values.ravel()
        X_test = pd.read_csv(model_data_dir / "X_test.csv")
        y_test = pd.read_csv(model_data_dir / "y_test.csv").values.ravel()
        return X_train, y_train, X_test, y_test
    except FileNotFoundError as e:
        logging.error(f"Data files not found in {model_data_dir}. Please run the model preparation script first.")
        raise
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        raise ValueError("Failed to load data.") from e


def validate_data(X_train: pd.DataFrame, y_train: np.ndarray, X_test: pd.DataFrame, y_test: np.ndarray) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Validate the loaded data for consistency and quality.

    Args:
        X_train: Training features.
        y_train: Training targets.
        X_test: Testing features.
        y_test: Testing targets.

    Returns:
        Tuple of (X_train, X_test) with X_test potentially reindexed to match X_train column order.

    Raises:
        ValueError: If data validation fails.
    """
    # Ensure both X_train and X_test are pandas DataFrames
    if not isinstance(X_train, pd.DataFrame):
        raise ValueError("X_train must be a pandas DataFrame.")
    if not isinstance(X_test, pd.DataFrame):
        raise ValueError("X_test must be a pandas DataFrame.")
    
    # Check for empty datasets
    if len(X_train) == 0 or len(X_test) == 0:
        raise ValueError("Training or testing data is empty.")

    # Verify column sets are identical
    X_train_cols = set(X_train.columns)
    X_test_cols = set(X_test.columns)
    
    if X_train_cols != X_test_cols:
        missing_in_test = X_train_cols - X_test_cols
        extra_in_test = X_test_cols - X_train_cols
        error_msg = "Column sets differ between X_train and X_test."
        if missing_in_test:
            error_msg += f" Missing in X_test: {sorted(missing_in_test)}."
        if extra_in_test:
            error_msg += f" Extra in X_test: {sorted(extra_in_test)}."
        raise ValueError(error_msg)
    
    # Check if column order matches, reindex X_test if needed
    if not X_train.columns.equals(X_test.columns):
        logging.info("Column order differs between X_train and X_test. Reindexing X_test to match X_train.")
        X_test = X_test.reindex(columns=X_train.columns)

    # Validate lengths match between features and targets
    if len(y_train) != len(X_train):
        raise ValueError(f"Mismatch between X_train length ({len(X_train)}) and y_train length ({len(y_train)}).")
    if len(y_test) != len(X_test):
        raise ValueError(f"Mismatch between X_test length ({len(X_test)}) and y_test length ({len(y_test)}).")

    # Check for missing values in features
    if X_train.isnull().any().any() or X_test.isnull().any().any():
        raise ValueError("Missing values found in feature data. Please preprocess the data.")

    # Check for missing values in targets
    if pd.isnull(y_train).any() or pd.isnull(y_test).any():
        raise ValueError("Missing values found in target data. Please preprocess the data.")

    logging.info(f"Data validation passed. Training on {len(X_train)} samples, testing on {len(X_test)} samples.")
    return X_train, X_test


def optimize_data_types(X_train: pd.DataFrame, X_test: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Optimize data types for better performance.

    Args:
        X_train: Training features.
        X_test: Testing features.

    Returns:
        Tuple of optimized (X_train, X_test).
    """
    # Convert to float32 for memory efficiency
    X_train = X_train.astype('float32')
    X_test = X_test.astype('float32')
    return X_train, X_test


def train_model(X_train: pd.DataFrame, y_train: np.ndarray, n_estimators: int = 100, random_state: int = 42) -> RandomForestRegressor:
    """
    Train the Random Forest model.

    Args:
        X_train: Training features.
        y_train: Training targets.
        n_estimators: Number of trees in the forest.
        random_state: Random state for reproducibility.

    Returns:
        Trained model.
    """
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=-1  # Use all available cores
    )
    logging.info("Starting model training...")
    model.fit(X_train, y_train)
    logging.info("Model training completed.")
    return model


def evaluate_model(model: RandomForestRegressor, X_test: pd.DataFrame, y_test: np.ndarray) -> float:
    """
    Evaluate the model on test data.

    Args:
        model: Trained model.
        X_test: Testing features.
        y_test: Testing targets.

    Returns:
        Mean Absolute Error.
    """
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    logging.info(f"Model Mean Absolute Error (MAE): {mae:.2f}")
    logging.info(f"On average, predictions are +/- {mae:.2f} points from actual scores.")
    return mae


def save_model(model: RandomForestRegressor, model_output_dir: Path, model_name: str) -> None:
    """
    Save the trained model to disk.

    Args:
        model: Trained model.
        model_output_dir: Directory to save the model.
        model_name: Name of the model file.
    """
    model_output_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_output_dir / model_name
    joblib.dump(model, model_path)
    logging.info(f"Model saved to: {model_path}")


def main(model_data_dir: str, model_output_dir: str, model_name: str, n_estimators: int, log_level: str) -> None:
    """
    Main function to orchestrate the model training pipeline.

    Args:
        model_data_dir: Directory containing prepared data.
        model_output_dir: Directory to save the trained model.
        model_name: Name of the model file.
        n_estimators: Number of estimators for the model.
        log_level: Logging level.
    """
    setup_logging(log_level)

    logging.info("Starting FPL Oracle model training pipeline.")

    try:
        # Load and validate data
        X_train, y_train, X_test, y_test = load_data(Path(model_data_dir))
        X_train, X_test = validate_data(X_train, y_train, X_test, y_test)

        # Optimize data types
        X_train, X_test = optimize_data_types(X_train, X_test)

        # Train model
        model = train_model(X_train, y_train, n_estimators)

        # Evaluate model
        evaluate_model(model, X_test, y_test)

        # Save model
        save_model(model, Path(model_output_dir), model_name)

        logging.info("FPL Oracle model training pipeline completed successfully.")

    except Exception as e:
        logging.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train FPL Oracle predictive model.")
    parser.add_argument("--model-data-dir", type=str, default="../model_data", help="Directory containing prepared data.")
    parser.add_argument("--model-output-dir", type=str, default="../trained_models", help="Directory to save the trained model.")
    parser.add_argument("--model-name", type=str, default="fpl_oracle_model.joblib", help="Name of the model file.")
    parser.add_argument("--n-estimators", type=int, default=100, help="Number of estimators for Random Forest.")
    parser.add_argument("--log-level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Logging level.")

    args = parser.parse_args()
    main(args.model_data_dir, args.model_output_dir, args.model_name, args.n_estimators, args.log_level)