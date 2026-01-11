import streamlit as st
import pandas as pd
from scipy.stats import norm

# ======================================================
# STREAMLIT CONFIG (DOIT ETRE EN PREMIER)
# ======================================================
st.set_page_config(page_title="NBA Betting Dashboard", layout="wide")

# ======================================================
# LOAD DATA (CLOUD SAFE)
# ======================================================
@st.cache_data
def load_data():
    games = pd.read_parquet("data_export/games.parquet")
    agg = pd.read_parquet("data_export/agg.parquet")
    defense = pd.read_parquet("data_export/defense.parquet")
    props = pd.read_parquet("data_export/props.parquet")
    return games, agg, defense, props

games, agg, defense, props = load_data()

# ======================================================
# DEFENSE COEFFICIENT
# ======================================================
defense["DEF_COEF"] = defense["DEF_RATING"] / defense["DEF_RATING"].mean()

# ======================================================
# TITLE
# ======================================================
st.title("NBA Betting Dashboard")
st.write("NBA player analysis based on last 7 games")

st.divider()

# ======================================================
# PLAYER SELECTION
# ======================================================
st.subheader("Player selection")
player = st.selectbox("Choose a player", sorted(agg["PLAYER_NAME"].unique()))

p_games = games[games["PLAYER_NAME"] == player]
p_avg = agg[agg["PLAYER_NAME"] == player].iloc[0]

# ======================================================
# MATCH CONTEXT
# ======================================================
st.subheader("Match context")
opponent = st.selectbox("Opponent team", sorted(defense["TEAM"].unique()))
def_coef = defense[defense["TEAM"] == opponent]["DEF_COEF"].values[0]

st.write("Defense coefficient:", round(def_coef, 2))

st.divider()

# ======================================================
# RECENT STATS
# ======================================================
st.subheader("Recent stats (7 games)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Points", round(p_avg["PTS_AVG"], 1))
c2.metric("Rebounds", round(p_avg["REB_AVG"], 1))
c3.metric("Assists", round(p_avg["AST_AVG"], 1))
c4.metric("PRA", round(p_avg["PRA_AVG"], 1))

st.divider()

# ======================================================
# CHART
# ======================================================
st.subheader("Points evolution")
st.line_chart(p_games.set_index("GAME_DATE")["PTS"])

st.divider()

# ======================================================
# MARKET SELECTION
# ======================================================
st.subheader("Bet analysis")

market = st.selectbox("Market", ["PTS", "PRA", "AST", "REB"])

row = props[(props["PLAYER_NAME"] == player) & (props["STAT"] == market)].iloc[0]

line_prop = st.number_input(
    "Bookmaker line",
    value=float(round(row["MEAN"], 1))
)

mean = row["MEAN"] * def_coef
std = row["STD"]
if pd.isna(std) or std == 0:
    std = 1

prob_over = 1 - norm.cdf(line_prop, mean, std)
value = abs(prob_over - 0.5)

st.write("Adjusted mean:", round(mean, 2))
st.write("Over probability:", round(prob_over * 100, 1), "%")
st.write("Value estimate:", round(value * 100, 1), "%")

# ======================================================
# DECISION
# ======================================================
st.subheader("Model decision")

if prob_over >= 0.65:
    st.success("OVER strongly recommended")
elif prob_over <= 0.35:
    st.error("UNDER strongly recommended")
else:
    st.warning("No clear value")

st.divider()

# ======================================================
# BANKROLL STRATEGY
# ======================================================
st.subheader("Bankroll management")

bankroll = st.number_input("Total bankroll", value=500.0)
stake = bankroll * 0.02

st.write("Recommended stake (2%):", round(stake, 2))

st.divider()

# ======================================================
# WARNING
# ======================================================
st.write("This dashboard is a decision support tool. No guarantee of profit.")
