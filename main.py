import streamlit as st
import pandas as pd
import numpy as np

def calculate_profit_with_budget(row, selected_team, current_budget):
    """
    Calculate profit based on betting entire budget on selected team to win
    - If selected team plays HOME and wins (FTR='H'): profit using 1XBH odds
    - If selected team plays AWAY and wins (FTR='A'): profit using 1XBA odds  
    - If selected team loses or draws: lose entire budget
    """
    if row['HomeTeam'] == selected_team and row['FTR'] == 'H':
        # Our team played home and won
        return (current_budget * row['1XBH']) - current_budget
    elif row['AwayTeam'] == selected_team and row['FTR'] == 'A':
        # Our team played away and won
        return (current_budget * row['1XBA']) - current_budget
    else:
        # Our team lost or drew - lose entire budget
        return -current_budget

def main():
    st.title("Football Betting Analysis")
    st.markdown("Upload your CSV file and analyze betting profits for any team!")
    
    # File upload
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        try:
            # Read the CSV
            df = pd.read_csv(uploaded_file)
            
            st.success(f"File uploaded successfully! {len(df)} matches found.")
            
            # Show basic info about the dataset
            st.subheader("Dataset Overview")
            st.write(f"**Total matches:** {len(df)}")
            st.write(f"**Columns:** {', '.join(df.columns.tolist())}")
            
            # Check if required columns exist
            required_columns = ['HomeTeam', 'AwayTeam', 'FTR', '1XBH', '1XBA']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                st.error(f"Missing required columns: {', '.join(missing_columns)}")
                st.info("Required columns: HomeTeam, AwayTeam, FTR, 1XBH, 1XBA")
                return
            
            # Get all unique teams
            all_teams = sorted(list(set(df['HomeTeam'].unique()) | set(df['AwayTeam'].unique())))
            
            # Team selection
            st.subheader("Select Team and Betting Strategy")
            
            col1, col2 = st.columns(2)
            
            with col1:
                selected_team = st.selectbox("Choose a team to analyze:", all_teams)
            
            with col2:
                initial_budget = st.number_input("Initial Budget (€)", min_value=1.0, value=100.0, step=10.0)
            
            # Cash out strategy
            st.subheader("Cash Out Strategy")
            
            col1, col2 = st.columns(2)
            
            with col1:
                cash_out_type = st.selectbox(
                    "Cash out method:",
                    ["After fixed number of games", "When reaching profit threshold", "No cash out (play all games)"]
                )
            
            with col2:
                if cash_out_type == "After fixed number of games":
                    cash_out_value = st.number_input("Number of games to play:", min_value=1, value=5, step=1)
                elif cash_out_type == "When reaching profit threshold":
                    cash_out_value = st.number_input("Cash out at profit % of initial budget:", min_value=10, value=200, step=10)
                else:
                    cash_out_value = None
            
            if selected_team:
                # Filter matches for selected team
                team_matches = df[(df['HomeTeam'] == selected_team) | (df['AwayTeam'] == selected_team)].copy()
                
                if len(team_matches) == 0:
                    st.warning(f"No matches found for {selected_team}")
                    return
                
                # Sort matches by date if available
                if 'Date' in team_matches.columns:
                    team_matches = team_matches.sort_values('Date').reset_index(drop=True)
                
                # Calculate progressive betting with compound profits
                current_budget = initial_budget
                budgets = []
                profits = []
                cash_out_reason = None
                games_played = 0
                
                for index, row in team_matches.iterrows():
                    games_played += 1
                    profit = calculate_profit_with_budget(row, selected_team, current_budget)
                    budgets.append(current_budget)
                    profits.append(profit)
                    
                    # Update budget for next bet
                    current_budget += profit
                    
                    # Check cash out conditions
                    should_cash_out = False
                    
                    # Check if budget goes to zero or negative
                    if current_budget <= 0:
                        current_budget = 0
                        cash_out_reason = f"Budget went to zero after {games_played} games"
                        should_cash_out = True
                    
                    # Check fixed number of games
                    elif cash_out_type == "After fixed number of games" and games_played >= cash_out_value:
                        cash_out_reason = f"Cashed out after {cash_out_value} games as planned"
                        should_cash_out = True
                    
                    # Check profit threshold
                    elif cash_out_type == "When reaching profit threshold":
                        profit_percentage = ((current_budget - initial_budget) / initial_budget) * 100
                        if profit_percentage >= cash_out_value:
                            cash_out_reason = f"Cashed out after reaching {cash_out_value}% profit threshold ({profit_percentage:.1f}% achieved)"
                            should_cash_out = True
                    
                    if should_cash_out:
                        break
                
                # If no cash out occurred and we played all games
                if cash_out_reason is None:
                    if cash_out_type == "No cash out (play all games)":
                        cash_out_reason = f"Played all {games_played} available games"
                    else:
                        cash_out_reason = f"Played all {games_played} available games (cash out condition not met)"
                
                # Add columns to dataframe
                team_matches = team_matches.iloc[:len(budgets)].copy()
                team_matches['Budget_Before'] = budgets
                team_matches['Profit'] = profits
                team_matches['Budget_After'] = [b + p for b, p in zip(budgets, profits)]
                
                # Add additional info columns
                team_matches['Home_or_Away'] = team_matches.apply(
                    lambda row: 'Home' if row['HomeTeam'] == selected_team else 'Away', axis=1
                )
                team_matches['Result'] = team_matches.apply(
                    lambda row: 'Win' if row['Profit'] > 0 else 'Loss/Draw', axis=1
                )
                
                # Display results
                st.subheader(f"Results for {selected_team}")
                
                # Show cash out reason
                if cash_out_reason:
                    if "went to zero" in cash_out_reason:
                        st.error(f"RESULT: {cash_out_reason}")
                    elif "reaching" in cash_out_reason:
                        st.success(f"RESULT: {cash_out_reason}")
                    else:
                        st.info(f"RESULT: {cash_out_reason}")
                
                # Summary statistics
                col1, col2, col3, col4 = st.columns(4)
                
                total_matches = len(team_matches)
                games_actually_played = len(budgets)
                final_budget = team_matches['Budget_After'].iloc[-1] if len(team_matches) > 0 else initial_budget
                total_profit = final_budget - initial_budget
                wins = len(team_matches[team_matches['Profit'] > 0])
                
                with col1:
                    st.metric("Games Available", total_matches)
                with col2:
                    st.metric("Games Played", games_actually_played)
                with col3:
                    st.metric("Initial Budget", f"€{initial_budget:.2f}")
                with col4:
                    st.metric("Final Budget", f"€{final_budget:.2f}")
                
                # Additional metrics
                col1, col2, col3, col4 = st.columns(4)
                
                win_rate = (wins / games_actually_played) * 100 if games_actually_played > 0 else 0
                
                with col1:
                    st.metric("Total Profit", f"€{total_profit:.2f}")
                with col2:
                    st.metric("Wins", f"{wins}/{games_actually_played}")
                with col3:
                    st.metric("Win Rate", f"{win_rate:.1f}%")
                with col4:
                    roi = (total_profit / initial_budget) * 100
                    st.metric("ROI", f"{roi:.1f}%")
                
                # Show multiplier and cash out info
                col1, col2 = st.columns(2)
                
                with col1:
                    if final_budget > 0:
                        multiplier = final_budget / initial_budget
                        st.metric("Budget Multiplier", f"{multiplier:.2f}x")
                    else:
                        st.metric("Budget Multiplier", "0x")
                
                with col2:
                    # Show what the strategy was
                    if cash_out_type == "After fixed number of games":
                        st.metric("Strategy", f"Cash out after {cash_out_value} games")
                    elif cash_out_type == "When reaching profit threshold":
                        st.metric("Strategy", f"Cash out at {cash_out_value}% profit")
                    else:
                        st.metric("Strategy", "Play all games")
                
                # Detailed breakdown
                st.subheader("Detailed Breakdown")
                
                # Home vs Away performance
                home_matches = team_matches[team_matches['Home_or_Away'] == 'Home']
                away_matches = team_matches[team_matches['Home_or_Away'] == 'Away']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Home Performance**")
                    if len(home_matches) > 0:
                        home_wins = len(home_matches[home_matches['Profit'] > 0])
                        home_win_rate = (home_wins / len(home_matches)) * 100
                        st.write(f"Matches: {len(home_matches)}")
                        st.write(f"Wins: {home_wins}")
                        st.write(f"Win Rate: {home_win_rate:.1f}%")
                    else:
                        st.write("No home matches found")
                
                with col2:
                    st.write("**Away Performance**")
                    if len(away_matches) > 0:
                        away_wins = len(away_matches[away_matches['Profit'] > 0])
                        away_win_rate = (away_wins / len(away_matches)) * 100
                        st.write(f"Matches: {len(away_matches)}")
                        st.write(f"Wins: {away_wins}")
                        st.write(f"Win Rate: {away_win_rate:.1f}%")
                    else:
                        st.write("No away matches found")
                
                # Show detailed results table
                st.subheader("Match Details")
                
                # Select columns to display
                display_columns = []
                available_columns = ['Date', 'Time', 'HomeTeam', 'AwayTeam', '1XBH', '1XBA', 'FTR', 'Home_or_Away', 'Result', 'Budget_Before', 'Profit', 'Budget_After']
                
                for col in available_columns:
                    if col in team_matches.columns:
                        display_columns.append(col)
                
                # Format the dataframe for better display
                display_df = team_matches[display_columns].copy()
                
                # Round budget columns to 2 decimal places for better display
                budget_cols = ['Budget_Before', 'Profit', 'Budget_After']
                for col in budget_cols:
                    if col in display_df.columns:
                        display_df[col] = display_df[col].round(2)
                
                # Display the table
                st.dataframe(
                    display_df,
                    use_container_width=True
                )
                
                # Download results
                st.subheader("Download Results")
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label=f"Download {selected_team} betting results as CSV",
                    data=csv,
                    file_name=f"{selected_team}_compound_betting_analysis.csv",
                    mime="text/csv"
                )
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.info("Please make sure your CSV file has the correct format and required columns.")

if __name__ == "__main__":
    main()