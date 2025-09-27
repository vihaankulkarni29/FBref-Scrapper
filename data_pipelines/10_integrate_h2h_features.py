import pandas as pd
import os
import logging
import numpy as np

def get_h2h_stats(home_team, away_team, date, h2h_df):
    """
    Calculates historical H2H stats for a given matchup before a specific date.
    """
    # Find all historical matches between the two teams before the match date
    historical_matches = h2h_df[
        (((h2h_df['Team'] == home_team) & (h2h_df['Opponent'] == away_team)) |
         ((h2h_df['Team'] == away_team) & (h2h_df['Opponent'] == home_team))) &
        (h2h_df['Date'] < date)
    ].copy()

    if historical_matches.empty:
        return pd.Series([0, 0, 0], index=['h2h_matches_played', 'h2h_home_win_pct', 'h2h_avg_goals'])

    # Determine home team wins
    home_wins = historical_matches[
        ((historical_matches['Team'] == home_team) & (historical_matches['Result'] == 'W')) |
        ((historical_matches['Opponent'] == home_team) & (historical_matches['Result'] == 'L'))
    ].shape[0]

    # Calculate home team average goals
    home_goals = historical_matches.apply(
        lambda row: row['Goals_For'] if row['Team'] == home_team else row['Goals_Against'], 
        axis=1
    ).mean()

    matches_played = len(historical_matches)
    win_pct = home_wins / matches_played if matches_played > 0 else 0
    
    return pd.Series([matches_played, win_pct, home_goals], index=['h2h_matches_played', 'h2h_home_win_pct', 'h2h_avg_goals'])

def main():
    """
    Integrates H2H stats into the main player dataset to create a final,
    feature-rich dataset for modeling.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # --- Configuration ---
    PROCESSED_DIR = "processed_data"
    PLAYER_DATA_FILE = "master_player_stats_v2.csv"
    FIXTURE_DATA_FILE = "fixtures_master.csv"
    H2H_DATA_FILE = "h2h_master.csv"
    OUTPUT_FILE = "master_player_stats_v4_h2h_features.csv"

    # --- Load Data ---
    logging.info("Loading all necessary datasets...")
    try:
        player_df = pd.read_csv(os.path.join(PROCESSED_DIR, PLAYER_DATA_FILE))
        fixture_df = pd.read_csv(os.path.join(PROCESSED_DIR, FIXTURE_DATA_FILE))
        h2h_df = pd.read_csv(os.path.join(PROCESSED_DIR, H2H_DATA_FILE))
    except FileNotFoundError as e:
        logging.error(f"Required data file not found: {e}. Please ensure all previous scripts have run.")
        return

    # --- FIX: Convert date and numeric columns robustly ---
    logging.info("Parsing dates and ensuring numeric types...")
    h2h_df['Date'] = pd.to_datetime(h2h_df['Date'], format='mixed', dayfirst=True)
    fixture_df['Date'] = pd.to_datetime(fixture_df['Date'], format='mixed', dayfirst=True)
    
    # This is the critical fix to prevent the TypeError
    h2h_df['Goals_For'] = pd.to_numeric(h2h_df['Goals_For'], errors='coerce')
    h2h_df['Goals_Against'] = pd.to_numeric(h2h_df['Goals_Against'], errors='coerce')
    
    # --- 1. Engineer H2H Features for each Fixture ---
    logging.info("Engineering H2H features for each historical fixture...")
    h2h_features = fixture_df.apply(
        lambda row: pd.concat([
            get_h2h_stats(row['Home'], row['Away'], row['Date'], h2h_df).rename({
                'h2h_home_win_pct': 'h2h_home_win_pct_home',
                'h2h_avg_goals': 'h2h_avg_goals_home'
            }),
            get_h2h_stats(row['Away'], row['Home'], row['Date'], h2h_df).rename({
                'h2h_home_win_pct': 'h2h_home_win_pct_away',
                'h2h_avg_goals': 'h2h_avg_goals_away'
            })
        ]),
        axis=1
    )
    fixture_df_h2h = pd.concat([fixture_df, h2h_features], axis=1)
    
    # --- 2. Merge H2H Context with Player Data ---
    logging.info("Merging H2H context with player data...")
    
    home_h2h = fixture_df_h2h.groupby(['Season', 'Home'])[['h2h_home_win_pct_home', 'h2h_avg_goals_home']].mean().reset_index().rename(columns={'Home': 'Squad'})
    away_h2h = fixture_df_h2h.groupby(['Season', 'Away'])[['h2h_home_win_pct_away', 'h2h_avg_goals_away']].mean().reset_index().rename(columns={'Away': 'Squad'})
    
    team_h2h_avg = pd.merge(home_h2h, away_h2h, on=['Season', 'Squad'], suffixes=('_home_avg', '_away_avg'))
    
    final_df = pd.merge(player_df, team_h2h_avg, on=['Season', 'Squad'], how='left')
    # Fill NaNs only in the added H2H numeric columns to avoid converting categorical NaNs to 0
    h2h_columns = ['h2h_home_win_pct_home', 'h2h_avg_goals_home', 'h2h_home_win_pct_away', 'h2h_avg_goals_away']
    final_df[h2h_columns] = final_df[h2h_columns].fillna(0)

    # --- 3. Re-calculate Final Features ---
    logging.info("Re-calculating final predictive features...")
    final_df['90s'] = final_df['Min'] / 90
    
    final_df['xG_p90'] = np.where(final_df['90s'] > 0, final_df['xG'] / final_df['90s'], 0)
    final_df['xAG_p90'] = np.where(final_df['90s'] > 0, final_df['xAG'] / final_df['90s'], 0)
    
    final_df['Gls_minus_xG'] = final_df['Gls'] - final_df['xG']
    final_df['Ast_minus_xAG'] = final_df['Ast'] - final_df['xAG']
    
    final_df['Position'] = final_df['Pos'].apply(lambda x: 'FWD' if 'FW' in str(x) else ('MID' if 'MF' in str(x) else ('DEF' if 'DF' in str(x) else 'GK')))
    
    final_df.replace([np.inf, -np.inf], 0, inplace=True)
    
    # --- Save the Final Dataset ---
    output_path = os.path.join(PROCESSED_DIR, OUTPUT_FILE)
    final_df.to_csv(output_path, index=False)
    
    logging.info("\n--- H2H Feature Integration Complete ---")
    logging.info(f"Final dataset with {len(final_df.columns)} columns created.")
    logging.info(f"Saved to: {output_path}")

if __name__ == '__main__':
    main()

