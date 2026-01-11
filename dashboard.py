import streamlit as st
import pandas as pd
from scipy.stats import norm

# STREAMLIT CONFIG (FIRST)
st.set_page_config(page_title="NBA Betting Dashboard", layout="wide")

# LOAD DATA (NO API CALLS)
@st.cache_data
def load_data():
    games = pd.read_parquet("data_export/games.parquet")
    agg = pd.read_parquet("data_export/agg.parquet")
    defense = pd.read_parquet("data_export/defense.parquet")
    props = pd.read_parquet("data_export/props.parquet")
    return games, agg, defense, props

games, agg, defense, props = load_data()

# TITLE
st.title("NBA Betting Dashboard")
st.write("NBA player analysis based on last 7 games")

# PLAYER SELECT
st.subheader("Player selection")
player = st.selectbox("Choose a player", sorted(agg["PLAYER_NAME"].unique()))

p_games = games[games["PLAYER_NAME"] == player]
p_avg = agg[agg["PLAYER_NAME"] == player].iloc[0]

# STATS
st.subheader("Recent stats (7 games)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Points", round(p_avg["PTS_AVG"], 1))
c2.metric("Rebounds", round(p_avg["REB_AVG"], 1))
c3.metric("Assists", round(p_avg["AST_AVG"], 1))
c4.metric("PRA", round(p_avg["PRA_AVG"], 1))

# CHART
st.subheader("Points evolution (last games)")
st.line_chart(p_games.set_index("GAME_DATE")["PTS"])

# BET MODEL PTS
st.subheader("Over Under analysis - Points")
line_pts = st.number_input("Bookmaker line (PTS)", value=float(round(p_avg["PTS_AVG"], 1)))

mean_pts = p_games["PTS"].mean()
std_pts = p_games["PTS"].std()
if pd.isna(std_pts) or std_pts == 0:
    std_pts = 5

prob_over_pts = 1 - norm.cdf(line_pts, mean_pts, std_pts)
st.write("Over probability:", round(prob_over_pts * 100, 1), "%")

if prob_over_pts >= 65:
    st.success("Strong OVER")
elif prob_over_pts <= 35:
    st.error("Strong UNDER")
else:
    st.warning("No clear value")

# OTHER MARKETS
st.subheader("Other markets")
market = st.selectbox("Market", ["PTS", "PRA", "AST", "REB"])

row = props[(props["PLAYER_NAME"] == player) & (props["STAT"] == market)].iloc[0]


