# FPL Data Analytics Pipeline

This repository contains a complete, automated data pipeline for collecting, cleaning, and preparing Fantasy Premier League (FPL) relevant football data from FBREF. The goal of this project is to create a feature-rich dataset ready for predictive modeling to gain an analytical edge in FPL.

## Project Overview

The pipeline is composed of four sequential Python scripts, each performing a specific task in the data workflow.

### The Data Pipeline

1.  **`01_fbref_scraper.py`**: A robust, block-resistant web scraper that uses Selenium to extract multiple seasons of detailed player statistics from FBREF.com. It handles anti-scraping measures like User-Agent rotation and can be configured for proxies.
2.  **`02_data_processing.py`**: Takes the raw CSV files from the scraper, cleans messy multi-level headers, merges all stat tables for each season, and consolidates them into a single, clean master file.
3.  **`03_feature_engineering.py`**: Reads the clean master file and engineers advanced predictive features, such as "per 90 minutes" metrics (`xG_p90`), efficiency ratios (`Gls_minus_xG`), and simplified positional groupings.
4.  **`04_model_data_prep.py`**: The final step in the pipeline. It calculates a proxy `FantasyPoints` target variable, selects the most predictive features, performs one-hot encoding on categorical data, and splits the data into training and testing sets, ready for a machine learning model.

### How to Run

1.  Clone the repository.
2.  Install the required dependencies: `pip install -r requirements.txt`
3.  Run the scripts in numerical order, located in the `data_pipelines/` directory.