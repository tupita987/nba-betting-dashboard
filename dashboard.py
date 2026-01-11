import streamlit as st
import pandas as pd
from scipy.stats import norm

# ======================================================
# CONFIG STREAMLIT (DOIT ETRE EN PREMIER)
# ======================================================
st.set_page_config(
    page_title="NBA Betting Dashboard",
    layout="wide"
)

# ======================================================
# CHARGEMENT DES DONNEES (PARQUET - CLOUD SAFE)
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
# TITRE & INTRO
# ======================================================
st.title("NBA Betting Dashboard")

st.markdown("""
Analyse des performances joueurs NBA  
Modele probabiliste base sur les 7 derniers matchs
""")

# ======================================================
# SELECTION DU JOUEUR
# ======================================================
st.subheader("Selection du joueur")

player = st.selectbox(
    "Choisir un joueur",
    sorted(agg["PLAYER_NAME"].unique())
)

p_games = games[games["PLAYER_NAME"] == player]
p_avg = agg[agg["PLAYER_NAME"] == player].iloc[0]

# ======================================================
# STATISTIQUES RECENTES
# ======================================================
st.subheader("Statistiques recentes (7 matchs)")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Points", round(p_avg["PTS_AVG"], 1))
c2.metric("Rebonds", round(p_avg["REB_AVG"], 1))
c3.metric("Passes", round(p_avg["AST_AVG"], 1))
c4.metric("PRA", round(p_avg["PRA_AVG"], 1))

# ======================================================
# GRAPHIQUE
# ======================================================
st.subheader("Evolution des points (7 derniers matchs)")
st.line_chart(p_games.set_index("GAME_DATE")["PTS"])

# ======================================================
# MODELE OVER / UNDER - POINTS
# ======================================================
st.subheader("Analyse du pari - Points (PTS)")

line_pts = st.number_input(
    "Ligne bookmaker (PTS)",
    value=float(round(p_avg["PTS_AVG"], 1))
)

mean_pts = p_games["PTS"].mean()
std_pts = p_games["PTS"].std()
if pd.isna(std_pts) or std_pts == 0:
    std_pts = 5

prob_over_pts = 1 - norm.cdf(line_pts, mean_pts, std_pts)

st.write(f"Probabilite Over : **{round(prob_over_pts * 100, 1)} %**")

if prob_over_pts >= 0.65:
    st.success("OVER fortement recommande")
elif prob_over_pts <= 0.35:
    st.error("UNDER fortement recommande")
else:
    st.warning("Aucune value claire")

# ======================================================
# AUTRES MARCHES : PRA / AST / REB
# ======================================================
st.subheader("Anal
