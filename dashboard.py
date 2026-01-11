import streamlit as st
import pandas as pd
from scipy.stats import norm

from analysis.fetch_data_cloud import load_players_games
from analysis.defense_cloud import load_team_defense

# MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="Tableau de bord Paris NBA",
    layout="wide"
)

@st.cache_data(ttl=3600)
def load_all_data():
    games = load_players_games(max_players=30)
    defense = load_team_defense()
    return games, defense

# LOAD DATA
with st.spinner("Chargement des donnees NBA..."):
    games, defense = load_all_data()

st.success("Donnees NBA chargees")

# SAFETY CHECK
required_cols = ["PLAYER_NAME", "PTS", "REB", "AST", "MIN"]

if games.empty:
    st.error("Aucune donnee joueur chargee depuis l'API NBA")
    st.stop()

missing = [c for c in required_cols if c not in games.columns]
if missing:
    st.error(f"Colonnes manquantes dans games: {missing}")
    st.stop()

# PRA
games["PRA"] = games["PTS"] + games["REB"] + games["AST"]

# AGGREGATION
agg = (
    games
    .groupby("PLAYER_NAME")
    .agg(
        PTS_AVG=("PTS", "mean"),
        REB_AVG=("REB", "mean"),
        AST_AVG=("AST", "mean"),
        PRA_AVG=("PRA", "mean"),
        MIN_AVG=("MIN", "mean")
    )
    .reset_index()
)

st.title("Tableau de bord Paris NBA - Mode Cloud")

# DEBUG (TEMPORAIRE)
st.subheader("Apercu donnees joueurs")
st.write(agg.head())

# PLAYER SELECTION
player = st.selectbox(
    "Choisir un joueur",
    sorted(agg["PLAYER_NAME"].unique())
)

p_games = games[games["PLAYER_NAME"] == player]

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("PTS AVG", round(p_games["PTS"].mean(), 1))
c2.metric("REB AVG", round(p_games["REB"].mean(), 1))
c3.metric("AST AVG", round(p_games["AST"].mean(), 1))
c4.metric("PRA AVG", round(p_games["PRA"].mean(), 1))

# CHART
st.subheader("Points - derniers matchs")
st.line_chart(p_games.set_index("GAME_DATE")["PTS"])

# BET MODEL
st.subheader("Analyse Over / Under (PTS)")
line = st.number_input("Ligne bookmaker", value=float(round(p_games["PTS"].mean(), 1)))

mean = p_games["PTS"].mean()
std = p_games["PTS"].std() or 5

prob_over = 1 - norm.cdf(line, mean, std)

st.write("Probabilite Over :", round(prob_over * 100, 1), "%")

if prob_over > 0.6:
    st.success("OVER recommande")
elif prob_over < 0.4:
    st.error("UNDER recommande")
else:
    st.warning("Pas de value claire")
