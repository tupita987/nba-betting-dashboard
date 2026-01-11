import streamlit as st
import pandas as pd
from scipy.stats import norm

from analysis.today_games import get_today_games
from analysis.b2b import is_back_to_back

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(page_title="Dashboard Paris NBA - AUTO", layout="wide")

# ======================================================
# LOAD DATA
# ======================================================
@st.cache_data(ttl=3600)
def load_all():
    games = pd.read_parquet("data_export/games.parquet")
    agg = pd.read_parquet("data_export/agg.parquet")
    defense = pd.read_parquet("data_export/defense.parquet")
    props = pd.read_parquet("data_export/props.parquet")
    today_games = get_today_games()
    return games, agg, defense, props, today_games

games, agg, defense, props, today_games = load_all()

games["PRA"] = games["PTS"] + games["REB"] + games["AST"]
defense["COEF_DEF"] = defense["DEF_RATING"] / defense["DEF_RATING"].mean()

# ======================================================
# TITRE
# ======================================================
st.title("Tableau de bord Paris NBA — Automatique")
st.write("PRA • OVER uniquement • domicile & B2B auto")

st.divider()

# ======================================================
# SELECTION JOUEUR
# ======================================================
player = st.selectbox("Choisir un joueur", sorted(agg["PLAYER_NAME"].unique()))
p_row = agg[agg["PLAYER_NAME"] == player].iloc[0]
p_games = games[games["PLAYER_NAME"] == player]

team_id = p_row["TEAM_ID"]
team_name = p_row["TEAM_NAME"]

# ======================================================
# CONTEXTE AUTOMATIQUE VIA today_games
# ======================================================
home = team_name in today_games["HOME_TEAM_NAME"].values
coef_home = 1.05 if home else 0.97

try:
    b2b = is_back_to_back(team_id)
except:
    b2b = False

coef_fatigue = 0.96 if b2b else 1.0

opponent = st.selectbox("Equipe adverse", sorted(defense["TEAM"].unique()))
coef_def = defense[defense["TEAM"] == opponent]["COEF_DEF"].values[0]
coef_def = min(max(coef_def, 0.92), 1.08)

# ======================================================
# AFFICHAGE CONTEXTE
# ======================================================
st.subheader("Contexte détecté automatiquement")

c1, c2, c3 = st.columns(3)
c1.metric("Domicile", "Oui" if home else "Non")
c2.metric("Back-to-back", "Oui" if b2b else "Non")
c3.metric("Adversaire", opponent)

st.divider()

# ======================================================
# STATS
# ======================================================
st.subheader("Statistiques (7 derniers matchs)")

c1, c2, c3, c4 = st.columns(4)
c1.metric("PTS", round(p_row["PTS_AVG"], 1))
c2.metric("REB", round(p_row["REB_AVG"], 1))
c3.metric("AST", round(p_row["AST_AVG"], 1))
c4.metric("PRA", round(p_row["PRA_AVG"], 1))

# ======================================================
# ANALYSE PRA
# ======================================================
st.subheader("Analyse PRA (OVER uniquement)")

row = props[(props["PLAYER_NAME"] == player) & (props["STAT"] == "PRA")].iloc[0]
line = st.number_input("Ligne bookmaker PRA", value=float(round(row["MEAN"], 1)))

mean_adj = row["MEAN"] * coef_def * coef_home * coef_fatigue
std = row["STD"] if row["STD"] > 0 else 1

prob_over = 1 - norm.cdf(line, mean_adj, std)
value = abs(prob_over - 0.5)
p90 = p_games["PRA"].quantile(0.9)

st.write("Moyenne ajustée :", round(mean_adj, 2))
st.write("Probabilité Over :", round(prob_over * 100, 1), "%")
st.write("Value estimée :", round(value * 100, 1), "%")
st.write("P90 PRA :", round(p90, 1))

# ======================================================
# DECISION FINALE
# ======================================================
decision = "NO BET"

if prob_over >= 0.57 and value >= 0.12:
    if p90 <= line + 8:
        decision = "OVER"

# ======================================================
# MISE
# ======================================================
bankroll = st.number_input("Bankroll totale", value=500.0)

stake = 0
if decision == "OVER":
    stake = bankroll * (0.03 if prob_over >= 0.62 else 0.015)

# ======================================================
# RESULTAT
# ======================================================
st.subheader("Décision du modèle")

if decision == "OVER":
    st.success("PARI AUTORISÉ : OVER PRA")
    st.write("Mise recommandée :", round(stake, 2))
else:
    st.warning("NO BET — aucun avantage détecté")

st.divider()
st.write("Outil d'aide à la décision — discipline obligatoire.")