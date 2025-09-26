# FPL Data Analytics Pipeline

This repository contains a complete, automated data pipeline for collecting, cleaning, preparing, training, and predicting Fantasy Premier League (FPL) relevant football data from FBREF. The goal of this project is to create a feature-rich dataset, train a predictive model, and generate FPL point predictions to gain an analytical edge in FPL.

## Project Overview

The pipeline is composed of eight Python scripts, with the first six forming the core sequential workflow for data processing and prediction, and the last two providing additional data scraping tools for enhanced analysis.

### The Data Pipeline

1.  **`01_fbref_scraper.py`**: A robust, block-resistant web scraper that uses Selenium to extract multiple seasons of detailed player statistics from FBREF.com. It handles anti-scraping measures like User-Agent rotation and can be configured for proxies.
2.  **`02_data_processing.py`**: Takes the raw CSV files from the scraper, cleans messy multi-level headers, merges all stat tables for each season, and consolidates them into a single, clean master file.
3.  **`03_feature_engineering.py`**: Reads the clean master file and engineers advanced predictive features, such as "per 90 minutes" metrics (`xG_p90`), efficiency ratios (`Gls_minus_xG`), and simplified positional groupings.
4.  **`04_model_data_prep.py`**: Prepares the data for modeling. It calculates a proxy `FantasyPoints` target variable, selects the most predictive features, performs one-hot encoding on categorical data, and splits the data into training and testing sets.
5.  **`05_train_model.py`**: Trains a Random Forest Regressor model on the prepared data. It loads the training and testing sets, trains the model, evaluates performance using Mean Absolute Error (MAE), and saves the trained model to the `trained_models/` directory.
6.  **`06_make_predictions.py`**: Loads the trained model and generates predictions on the latest player data. It prepares the prediction data to match the training format, makes predictions, and saves a sorted report of predicted FPL points to the `predictions/` directory.
7.  **`07_fixture_scraper.py`**: Scrapes and cleans Premier League fixture lists for multiple seasons from FBREF, including scores, xG, and match details. Saves a master CSV file to the `raw_data/` directory for fixture analysis.
8.  **`08_h2h_scraper.py`**: Scrapes head-to-head match logs for all Premier League teams across specified seasons, cleaning and saving individual CSV files for each team-season to the `raw_data/h2h/` directory for historical performance insights.

### Output Directories
- **`raw_data/`**: Contains scraped raw data files, including fixtures and head-to-head logs.
- **`processed_data/`**: Contains cleaned and feature-engineered data files.
- **`model_data/`**: Contains training and testing datasets (`X_train.csv`, `y_train.csv`, etc.).
- **`trained_models/`**: Contains the saved trained model (`fpl_oracle_model.joblib`).
- **`predictions/`**: Contains the prediction reports (`gameweek_predictions.csv`).

### How to Run

1.  Clone the repository.
2.  Install the required dependencies: `pip install -r requirements.txt`
3.  Run the core pipeline scripts (01-06) in numerical order, located in the `data_pipelines/` directory. Use `python data_pipelines/XX_script_name.py` from the project root.
4.  Optionally, run the additional scrapers (07-08) to collect supplementary data for enhanced analysis.