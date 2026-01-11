import streamlit as st
import pandas as pd
from scipy.stats import norm

# ======================================================
# CONFIG STREAMLIT
# ======================================================
st.set_page_config(page_title="Tableau de bord Paris NBA - V2", layout="wide")

# ======================================================
# LOAD DATA
# ======================================================
@st.cache_data
def charger_donnees():
    matchs = pd.read_parquet("data_export/games.parquet")
    moyennes = pd.read_parquet("data_export/agg.parquet")
    defenses = pd.read_parquet("data_export/defense.parquet")
    props = pd.read_parquet("data_export/props.parquet")
    return matchs, moyennes, defenses, props

matchs, moyennes, defenses, props = charger_donnees()

# ======================================================
# PREPARATION
# ======================================================
matchs["PRA"] = matchs["PTS"] + matchs["REB"] + matchs["AST"]
defenses["COEF_DEF"] = defenses["DEF_RATING"] / defenses["DEF_RATING"].mean()

# ======================================================
# TITRE
# ======================================================
st.title("Tableau de bord Paris NBA — V2")
st.write("Modele OVER-only PRA avec gestion du risque")

st.divider()

# ======================================================
# SELECTION JOUEUR
# ======================================================
joueur = st.selectbox("Choisir un joueur", sorted(moyennes["PLAYER_NAME"].unique()))

j_matchs = matchs[matchs["PLAYER_NAME"] == joueur]
j_moy = moyennes[moyennes["PLAYER_NAME"] == joueur].iloc[0]

# ======================================================
# CONTEXTE AUTOMATISE
# ======================================================
st.subheader("Contexte du match")

adversaire = st.selectbox("Equipe adverse", sorted(defenses["TEAM"].unique()))
coef_def = defenses[defenses["TEAM"] == adversaire]["COEF_DEF"].values[0]
coef_def = min(max(coef_def, 0.92), 1.08)

home = st.checkbox("Match a domicile", value=True)
coef_home = 1.05 if home else 0.97

fatigue = st.checkbox("Back-to-back (fatigue)", value=False)
coef_fatigue = 0.96 if fatigue else 1.0

# ======================================================
# STATS
# ======================================================
st.subheader("Statistiques recentes (7 matchs)")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Points", round(j_moy["PTS_AVG"], 1))
c2.metric("Rebonds", round(j_moy["REB_AVG"], 1))
c3.metric("Passes", round(j_moy["AST_AVG"], 1))
c4.metric("PRA", round(j_moy["PRA_AVG"], 1))

st.divider()

# ======================================================
# ANALYSE PRA
# ======================================================
st.subheader("Analyse du pari PRA (OVER uniquement)")

row = props[(props["PLAYER_NAME"] == joueur) & (props["STAT"] == "PRA")].iloc[0]

ligne_book = st.number_input("Ligne bookmaker PRA", value=float(round(row["MEAN"], 1)))

# Moyenne ajustee (contexte capé)
mean_adj = row["MEAN"] * coef_def * coef_home * coef_fatigue
std = row["STD"] if row["STD"] > 0 else 1

prob_over = 1 - norm.cdf(ligne_book, mean_adj, std)
value = abs(prob_over - 0.5)

# Filtre de risque P90
p90 = j_matchs["PRA"].quantile(0.9)

st.write("Moyenne ajustee :", round(mean_adj, 2))
st.write("Probabilite Over :", round(prob_over * 100, 1), "%")
st.write("Value estimee :", round(value * 100, 1), "%")
st.write("P90 PRA :", round(p90, 1))

st.divider()

# ======================================================
# DECISION (POINT 1 + 2)
# ======================================================
decision = "NO BET"

if prob_over >= 0.57 and value >= 0.12:
    if p90 <= ligne_book + 8:
        decision = "OVER"

# ======================================================
# MISE DYNAMIQUE (POINT 4)
# ======================================================
bankroll = st.number_input("Bankroll totale", value=500.0)

stake = 0
if decision == "OVER":
    if prob_over >= 0.62:
        stake = bankroll * 0.03
    else:
        stake = bankroll * 0.015

# ======================================================
# AFFICHAGE FINAL
# ======================================================
st.subheader("Decision finale du modele")

if decision == "OVER":
    st.success("PARI AUTORISE : OVER PRA")
    st.write("Mise recommandee :", round(stake, 2))
else:
    st.warning("NO BET — Pari refuse par le modele")

st.divider()

st.write(
    "Avertissement : ce tableau de bord est un outil d'aide a la decision. "
    "Il n'existe aucune garantie de gain. Discipline obligatoire."
)