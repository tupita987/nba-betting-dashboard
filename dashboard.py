import streamlit as st
import pandas as pd
from scipy.stats import norm

# MUST be first
st.set_page_config(page_title="NBA Betting Dashboard", layout="wide")

@st.cache_data
def load_data():
    games = pd.read_parquet("data_export/games.parquet")
    agg = pd.read_parquet("data_export/agg.parquet")
    defense = pd.read_parquet("data_export/defense.parquet")
    props = pd.read_parquet("data_export/props.parquet")
    return games, agg, defense, props

games, agg, defense, props = load_data()

st.title("NBA Betting Dashboard - Pro Cloud")

# Sélection joueur
player = st.selectbox("Choisir un joueur", sorted(agg["PLAYER_NAME"].unique()))

p_games = games[games["PLAYER_NAME"] == player]
p_avg = agg[agg["PLAYER_NAME"] == player].iloc[0]

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("PTS AVG", round(p_avg["PTS_AVG"], 1))
c2.metric("REB AVG", round(p_avg["REB_AVG"], 1))
c3.metric("AST AVG", round(p_avg["AST_AVG"], 1))
c4.metric("PRA AVG", round(p_avg["PRA_AVG"], 1))

# Graphique
st.subheader("Points derniers matchs")
st.line_chart(p_games.set_index("GAME_DATE")["PTS"])

# Modèle Over/Under
st.subheader("Analyse Over / Under (PTS)")
line = st.number_input("Ligne bookmaker", value=float(round(p_avg["PTS_AVG"], 1)))

mean = p_avg["PTS_AVG"]
std = p_games["PTS"].std() or 5

prob_over = 1 - norm.cdf(line, mean, std)
st.write("Probabilite Over :", round(prob_over * 100, 1), "%")

if prob_over > 0.6:
    st.success("OVER recommande")
elif prob_over < 0.4:
    st.error("UNDER recommande")
else:
    st.warning("Pas de value claire")
