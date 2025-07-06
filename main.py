import streamlit as st
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
            st.subheader("Select Team")
            selected_team = st.selectbox("Choose a team to analyze:", all_teams)
            
            if selected_team:
                # Filter matches for selected team
                team_matches = df[(df['HomeTeam'] == selected_team) | (df['AwayTeam'] == selected_team)].copy()
                
                if len(team_matches) == 0:
                    st.warning(f"No matches found for {selected_team}")
                    return
                
                # Calculate profits
                team_matches['Profit'] = team_matches.apply(
                    lambda row: calculate_profit(row, selected_team), axis=1
                )
                
                # Add additional info columns
                team_matches['Home_or_Away'] = team_matches.apply(
                    lambda row: 'Home' if row['HomeTeam'] == selected_team else 'Away', axis=1
                )
                team_matches['Result'] = team_matches.apply(
                    lambda row: 'Win' if row['Profit'] > 0 else 'Loss/Draw', axis=1
                )
                
                # Display results
                st.subheader(f"Results for {selected_team}")
                
                # Summary statistics
                col1, col2, col3, col4 = st.columns(4)
                
                total_matches = len(team_matches)
                total_profit = team_matches['Profit'].sum()
                wins = len(team_matches[team_matches['Profit'] > 0])
                win_rate = (wins / total_matches) * 100 if total_matches > 0 else 0
                
                with col1:
                    st.metric("Total Matches", total_matches)
                with col2:
                    st.metric("Total Profit", f"€{total_profit:.2f}")
                with col3:
                    st.metric("Wins", f"{wins}/{total_matches}")
                with col4:
                    st.metric("Win Rate", f"{win_rate:.1f}%")
                
                # Detailed breakdown
                st.subheader("Detailed Breakdown")
                
                # Home vs Away performance
                home_matches = team_matches[team_matches['Home_or_Away'] == 'Home']
                away_matches = team_matches[team_matches['Home_or_Away'] == 'Away']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Home Performance**")
                    if len(home_matches) > 0:
                        home_profit = home_matches['Profit'].sum()
                        home_wins = len(home_matches[home_matches['Profit'] > 0])
                        home_win_rate = (home_wins / len(home_matches)) * 100
                        st.write(f"Matches: {len(home_matches)}")
                        st.write(f"Profit: €{home_profit:.2f}")
                        st.write(f"Win Rate: {home_win_rate:.1f}%")
                    else:
                        st.write("No home matches found")
                
                with col2:
                    st.write("**Away Performance**")
                    if len(away_matches) > 0:
                        away_profit = away_matches['Profit'].sum()
                        away_wins = len(away_matches[away_matches['Profit'] > 0])
                        away_win_rate = (away_wins / len(away_matches)) * 100
                        st.write(f"Matches: {len(away_matches)}")
                        st.write(f"Profit: €{away_profit:.2f}")
                        st.write(f"Win Rate: {away_win_rate:.1f}%")
                    else:
                        st.write("No away matches found")
                
                # Show detailed results table
                st.subheader("Match Details")
                
                # Select columns to display
                display_columns = []
                available_columns = ['Date', 'Time', 'HomeTeam', 'AwayTeam', '1XBH', '1XBA', 'FTR', 'Home_or_Away', 'Result', 'Profit']
                
                for col in available_columns:
                    if col in team_matches.columns:
                        display_columns.append(col)
                
                # Display the table
                st.dataframe(
                    team_matches[display_columns].sort_values('Profit', ascending=False),
                    use_container_width=True
                )
                
                # Download results
                st.subheader("Download Results")
                csv = team_matches[display_columns].to_csv(index=False)
                st.download_button(
                    label=f"Download {selected_team} betting results as CSV",
                    data=csv,
                    file_name=f"{selected_team}_betting_analysis.csv",
                    mime="text/csv"
                )
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.info("Please make sure your CSV file has the correct format and required columns.")

if __name__ == "__main__":
    main()