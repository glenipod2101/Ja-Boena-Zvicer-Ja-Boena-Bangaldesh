import pandas as pd
import numpy as np

def calculate_profit(row, selected_team):
    """
    Calculate profit based on betting on selected team to win
    - If selected team plays HOME and wins (FTR='H'): profit using 1XBH odds
    - If selected team plays AWAY and wins (FTR='A'): profit using 1XBA odds  
    - If selected team loses or draws: -100 loss
    """
    if row['HomeTeam'] == selected_team and row['FTR'] == 'H':
        # Our team played home and won
        return ((100 * row['1XBH']) - 100)
    elif row['AwayTeam'] == selected_team and row['FTR'] == 'A':
        # Our team played away and won
        return ((100 * row['1XBA']) - 100)
    else:
        # Our team lost or drew
        return -100