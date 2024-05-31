import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64

# Title of the dashboard
st.title("Cricket Match Insights Dashboard")

# Load data stats
@st.cache_data
def load_data():
    each_ball_records_df = pd.read_csv('each_ball_records.csv')
    each_match_records_df = pd.read_csv('each_match_records.csv')
    return each_ball_records_df, each_match_records_df

each_ball_records_df, each_match_records_df = load_data()

# Data Preprocessing
each_match_records_df.fillna({'winner_runs': 0, 'winner_wickets': 0, 'man_of_match': 'No Award'}, inplace=True)
each_match_records_df['date'] = pd.to_datetime(each_match_records_df['date'], format='%d-%m-%Y')
each_ball_records_df['over'] = each_ball_records_df['over'].astype(str)
each_ball_records_df['over_number'] = each_ball_records_df['over'].str.split('.').str[0].astype(int)

# Sidebar filters
st.sidebar.header("Filters")

# Season filter
season_filter = st.sidebar.multiselect(
    "Select Season(s)",
    options=each_match_records_df["season"].unique(),
    default=each_match_records_df["season"].unique()
)

# Team filter
teams = sorted(set(each_match_records_df['team1']).union(set(each_match_records_df['team2'])))
team_filter = st.sidebar.multiselect(
    "Select Team(s)",
    options=teams,
    default=teams
)

# Date range filter
date_filter = st.sidebar.date_input(
    "Select Date Range",
    value=(each_match_records_df['date'].min().date(), each_match_records_df['date'].max().date()),
    min_value=each_match_records_df['date'].min().date(),
    max_value=each_match_records_df['date'].max().date()
)

# Convert date_filter to pandas Timestamp
start_date = pd.Timestamp(date_filter[0])
end_date = pd.Timestamp(date_filter[1])

# Select analysis type
analysis_type = st.sidebar.selectbox(
    "Select Analysis Type",
    ["Match Distribution", "Run Distribution", "Wicket Distribution", "Toss Analysis", "Match Outcomes", "Top Players"]
)

# Apply filters
filtered_match_df = each_match_records_df[
    (each_match_records_df["season"].isin(season_filter)) &
    (each_match_records_df["date"].between(start_date, end_date)) &
    ((each_match_records_df['team1'].isin(team_filter)) | (each_match_records_df['team2'].isin(team_filter)))
]
filtered_ball_df = each_ball_records_df[each_ball_records_df["match_no"].isin(filtered_match_df["match_number"])]

# Display filtered data
st.write(f"Total matches: {filtered_match_df.shape[0]}")
st.write(f"Total balls: {filtered_ball_df.shape[0]}")

# Analysis plots based on the selected type
if analysis_type == "Match Distribution":
    st.subheader('Distribution of Matches Across Seasons')
    st.markdown("This graph shows the distribution of matches across different seasons. You can see which seasons had the most matches.")
    season_count_plot = px.histogram(filtered_match_df, x='season', title='Distribution of Matches Across Seasons')
    season_count_plot.update_layout(xaxis_title='Season', yaxis_title='Number of Matches')
    st.plotly_chart(season_count_plot)
    
    # Data table for matches
    st.write("Data Table for Matches:")
    st.write(filtered_match_df)

    st.subheader('Distribution of Matches Across Venues')
    st.markdown("This graph shows the distribution of matches across different venues. It helps in understanding which venues hosted the most matches.")
    venue_count_plot = px.histogram(filtered_match_df, y='venue', title='Distribution of Matches Across Venues', 
                                    category_orders={'venue': filtered_match_df['venue'].value_counts().index.tolist()})
    venue_count_plot.update_layout(xaxis_title='Number of Matches', yaxis_title='Venue')
    st.plotly_chart(venue_count_plot)

    # Data table for venues
    st.write("Data Table for Venues:")
    st.write(filtered_match_df[['venue']].value_counts().reset_index(name='Number of Matches'))

elif analysis_type == "Run Distribution":
    st.subheader('Distribution of Runs Scored Per Ball')
    st.markdown("This histogram shows the distribution of runs scored per ball. It gives an insight into how frequently different runs are scored.")
    runs_hist_plot = px.histogram(filtered_ball_df, x='score', nbins=30, title='Distribution of Runs Scored Per Ball', marginal='rug')
    runs_hist_plot.update_layout(xaxis_title='Runs', yaxis_title='Frequency')
    st.plotly_chart(runs_hist_plot)

    # Data table for runs scored per ball
    st.write("Data Table for Runs Scored Per Ball:")
    st.write(filtered_ball_df[['score']])

    st.subheader('Total Runs Scored Per Over')
    st.markdown("This line plot shows the total runs scored in each over. It helps in understanding the scoring patterns across different overs.")
    overs_summary = filtered_ball_df.groupby('over_number')['score'].sum()
    overs_summary_plot = px.line(x=overs_summary.index, y=overs_summary.values, title='Total Runs Scored Per Over')
    overs_summary_plot.update_layout(xaxis_title='Over Number', yaxis_title='Total Runs')
    st.plotly_chart(overs_summary_plot)

    # Data table for total runs scored per over
    st.write("Data Table for Total Runs Scored Per Over:")
    st.write(overs_summary.reset_index())

elif analysis_type == "Wicket Distribution":
    # Filter for wickets
    wickets_df = filtered_ball_df[filtered_ball_df['outcome'].str.contains('out', case=False, na=False)]

    st.subheader('Distribution of Wickets Taken Per Over')
    st.markdown("This histogram shows the distribution of wickets taken in each over. It provides insights into which overs are more likely to result in wickets.")
    wickets_hist_plot = px.histogram(wickets_df, x='over_number', nbins=20, title='Distribution of Wickets Taken Per Over')
    wickets_hist_plot.update_layout(xaxis_title='Over Number', yaxis_title='Frequency')
    st.plotly_chart(wickets_hist_plot)

    # Data table for wickets taken per over
    st.write("Data Table for Wickets Taken Per Over:")
    st.write(wickets_df.groupby('over_number').size().reset_index(name='Wickets'))

elif analysis_type == "Toss Analysis":
    toss_outcomes = filtered_match_df['toss_won'].value_counts()
    toss_decisions = filtered_match_df['toss_decision'].value_counts()

    st.subheader('Toss Winning Teams')
    st.markdown("This graph shows the number of times each team has won the toss. It highlights which teams are more successful in winning the toss.")
    toss_teams_plot = px.histogram(filtered_match_df, x='toss_won', title='Toss Winning Teams', 
                                   category_orders={'toss_won': toss_outcomes.index.tolist()})
    toss_teams_plot.update_layout(xaxis_title='Team', yaxis_title='Number of Times Toss Won')
    st.plotly_chart(toss_teams_plot)

    # Data table for toss winning teams
    st.write("Data Table for Toss Winning Teams:")
    st.write(toss_outcomes.reset_index(name='Number of Times Toss Won'))

    st.subheader('Toss Decisions')
    st.markdown("This graph shows the decisions made by the teams after winning the toss. It helps in understanding the preference of teams to bat or bowl first.")
    toss_decisions_plot = px.histogram(filtered_match_df, x='toss_decision', title='Toss Decisions', 
                                       category_orders={'toss_decision': toss_decisions.index.tolist()})
    toss_decisions_plot.update_layout(xaxis_title='Decision', yaxis_title='Number of Times Decision Made')
    st.plotly_chart(toss_decisions_plot)

    # Data table for toss decisions
    st.write("Data Table for Toss Decisions:")
    st.write(toss_decisions.reset_index(name='Number of Times Decision Made'))

elif analysis_type == "Match Outcomes":
    win_by_runs = filtered_match_df[filtered_match_df['winner_runs'] > 0]
    win_by_wickets = filtered_match_df[filtered_match_df['winner_wickets'] > 0]

    st.subheader('Match Winners')
    match_winners_plot = px.histogram(filtered_match_df, x='winner', title='Match Winners', 
                                      category_orders={'winner': filtered_match_df['winner'].value_counts().index.tolist()})
    match_winners_plot.update_layout(xaxis_title='Team', yaxis_title='Number of Wins')
    st.plotly_chart(match_winners_plot)

    st.subheader('Win Margin by Runs')
    win_by_runs_hist_plot = px.histogram(win_by_runs, x='winner_runs', nbins=30, title='Win Margin by Runs', marginal='rug')
    win_by_runs_hist_plot.update_layout(xaxis_title='Runs', yaxis_title='Frequency')
    st.plotly_chart(win_by_runs_hist_plot)

    st.subheader('Win Margin by Wickets')
    win_by_wickets_hist_plot = px.histogram(win_by_wickets, x='winner_wickets', nbins=10, title='Win Margin by Wickets', marginal='rug')
    win_by_wickets_hist_plot.update_layout(xaxis_title='Wickets', yaxis_title='Frequency')
    st.plotly_chart(win_by_wickets_hist_plot)

elif analysis_type == "Top Players":
    # Top batters
    top_batters = filtered_ball_df['batter'].value_counts().head(10)
    st.subheader('Top 10 Batters')
    top_batters_plot = px.bar(top_batters, x=top_batters.values, y=top_batters.index, orientation='h', title='Top 10 Batters')
    top_batters_plot.update_layout(xaxis_title='Number of Times Batted', yaxis_title='Batter')
    st.plotly_chart(top_batters_plot)

    # Top bowlers
    top_bowlers = filtered_ball_df['bowler'].value_counts().head(10)
    st.subheader('Top 10 Bowlers')
    top_bowlers_plot = px.bar(top_bowlers, x=top_bowlers.values, y=top_bowlers.index, orientation='h', title='Top 10 Bowlers')
    top_bowlers_plot.update_layout(xaxis_title='Number of Times Bowled', yaxis_title='Bowler')
    st.plotly_chart(top_bowlers_plot)

# Data export as CSV
st.sidebar.subheader("Export Data")
if st.sidebar.button("Export Data as CSV"):
    csv = filtered_match_df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="cricket_data.csv">Download CSV File</a>'
    st.sidebar.markdown(href, unsafe_allow_html=True)

#Footer
st.sidebar.markdown("""
---
*Created with Streamlit and Plotly*
""")
