# FPL Oracle: Fantasy Premier League Prediction Pipeline

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A comprehensive, automated data pipeline for Fantasy Premier League (FPL) analytics. This project scrapes football data from multiple sources, engineers predictive features, trains machine learning models, and generates FPL point predictions to provide analytical insights for fantasy football management.

## Project Overview

The pipeline is composed of fifteen Python scripts, forming the core sequential workflow for data processing, feature integration, and prediction, with additional tools for scraping supplementary data.

### The Data Pipeline

1.  **`01_fbref_scraper.py`**: A robust, block-resistant web scraper that uses Selenium to extract multiple seasons of detailed player statistics from FBREF.com. It handles anti-scraping measures like User-Agent rotation and can be configured for proxies. To specify a custom Chrome binary path (required on some systems), set the `CHROME_BINARY` environment variable (e.g., `export CHROME_BINARY=/path/to/chrome`). If not set, ChromeDriver will auto-detect the binary.
2.  **`02_data_processing.py`**: Takes the raw CSV files from the scraper, cleans messy multi-level headers, merges all stat tables for each season, and consolidates them into a single, clean master file.
3.  **`03_feature_engineering.py`**: Reads the clean master file and engineers advanced predictive features, such as "per 90 minutes" metrics (`xG_p90`), efficiency ratios (`Gls_minus_xG`), and simplified positional groupings.
4.  **`04_model_data_prep.py`**: Prepares the data for modeling. It calculates a proxy `FantasyPoints` target variable, selects the most predictive features, performs one-hot encoding on categorical data, and splits the data into training and testing sets.
5.  **`05_train_model.py`**: Trains a Random Forest Regressor model on the prepared data. It loads the training and testing sets, trains the model, evaluates performance using Mean Absolute Error (MAE), and saves the trained model to the `trained_models/` directory.
6.  **`06_make_predictions.py`**: Loads the trained model and generates predictions on the latest player data. It prepares the prediction data to match the training format, makes predictions, and saves a sorted report of predicted FPL points to the `predictions/` directory.
7.  **`07_fixture_scraper.py`**: Scrapes and cleans Premier League fixture lists for multiple seasons from FBREF, including scores, xG, and match details. Saves a master CSV file to the `raw_data/` directory for fixture analysis.
8.  **`08_h2h_scraper.py`**: Scrapes head-to-head match logs for all Premier League teams across specified seasons, cleaning and saving individual CSV files for each team-season to the `raw_data/h2h/` directory for historical performance insights.
9.  **`09_h2h_processing.py`**: Processes raw head-to-head match data, cleans it, removes duplicates, and creates a master H2H file for historical analysis.
10. **`10_integrate_h2h_features.py`**: Integrates head-to-head statistics into the main player dataset, engineering features like historical win percentages and average goals for enhanced predictive modeling.
11. **`11_model_data_prep_v4.py`**: Prepares the v4 dataset for modeling by calculating fantasy points, selecting features including new H2H metrics, applying one-hot encoding, and splitting into training and testing sets.
12. **`12_train_model_v4.py`**: Trains the v4 version of the Random Forest Regressor model using the enhanced dataset with H2H features, evaluates performance, and saves the improved model.
13. **`13_make_predictions_v4.py`**: Loads the trained v4 model with H2H features and generates predictions on the latest player data, saving a sorted report of predicted FPL points.
14. **`14_fpl_api_client.py`**: Connects to the official FPL API to fetch master player data and detailed gameweek histories, with improved error handling, timeouts, and retry logic for API reliability.
15. **`15_per_match_scraper.py`**: Scrapes per-match player performance data from FotMob for all historical fixtures, saving individual CSV files for each match.

### Output Directories
The following directories are created during pipeline execution:
- **`raw_data/`**: Scraped raw data files, including fixtures and head-to-head logs.
- **`processed_data/`**: Cleaned and feature-engineered data files, including master H2H data and integrated datasets.
- **`model_data/`**: Training and testing datasets (`X_train.csv`, `y_train.csv`, etc.).
- **`model_data_v4/`**: V4 training and testing datasets with H2H features.
- **`trained_models/`**: Saved trained models (`.joblib` files).
- **`predictions/`**: Prediction reports (`gameweek_predictions.csv`).

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/fpl-oracle.git
   cd fpl-oracle
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the pipeline scripts in sequence from the `data_pipelines/` directory:

```bash
# Core data collection and processing (01-06)
python data_pipelines/01_fbref_scraper.py
python data_pipelines/02_data_processing.py
# ... continue with 03-06

# Advanced features (07-13)
# ... run additional scripts as needed

# Predictions (14-16)
python data_pipelines/14_fpl_api_client.py
# ... etc.
```

**Note**: Scripts 01-12 form the complete workflow. Scripts 13-16 provide enhanced prediction capabilities.

## Data Sources

- **FBref.com**: Comprehensive player statistics
- **Fantasy Premier League API**: Official FPL data and gameweek histories
- **FotMob**: Per-match player performance data
- **Additional Scrapers**: Fixtures and head-to-head match logs

## Features

- Automated data scraping with anti-bot measures
- Advanced feature engineering (per-90 metrics, efficiency ratios)
- Head-to-head statistics integration
- Machine learning predictions using Random Forest
- Comprehensive data cleaning and processing pipeline

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This project is for educational and analytical purposes only. Always respect website terms of service and API usage policies.