import streamlit as st
import pandas as pd
from scipy.stats import norm

# ======================================================
# CONFIGURATION STREAMLIT (OBLIGATOIRE EN PREMIER)
# ======================================================
st.set_page_config(
    page_title="Tableau de bord Paris NBA",
    layout="wide"
)

# ======================================================
# CHARGEMENT DES DONNEES (CLOUD SAFE - PARQUET)
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
# COEFFICIENT DEFENSIF
# ======================================================
defenses["COEF_DEF"] = defenses["DEF_RATING"] / defenses["DEF_RATING"].mean()

# ======================================================
# TITRE
# ======================================================
st.title("Tableau de bord Paris NBA")
st.write("Analyse des joueurs NBA basee sur les 7 derniers matchs")

st.divider()

# ======================================================
# SELECTION DU JOUEUR
# ======================================================
st.subheader("Selection du joueur")

joueur = st.selectbox(
    "Choisir un joueur",
    sorted(moyennes["PLAYER_NAME"].unique())
)

j_matchs = matchs[matchs["PLAYER_NAME"] == joueur]
j_moy = moyennes[moyennes["PLAYER_NAME"] == joueur].iloc[0]

# ======================================================
# CONTEXTE DU MATCH
# ======================================================
st.subheader("Contexte du match")

adversaire = st.selectbox(
    "Equipe adverse",
    sorted(defenses["TEAM"].unique())
)

coef_def = defenses[defenses["TEAM"] == adversaire]["COEF_DEF"].values[0]

st.write("Coefficient defensif adverse :", round(coef_def, 2))

st.divider()

# ======================================================
# STATISTIQUES RECENTES
# ======================================================
st.subheader("Statistiques recentes (7 matchs)")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Points", round(j_moy["PTS_AVG"], 1))
c2.metric("Rebonds", round(j_moy["REB_AVG"], 1))
c3.metric("Passes", round(j_moy["AST_AVG"], 1))
c4.metric("PRA", round(j_moy["PRA_AVG"], 1))

st.divider()

# ======================================================
# GRAPHIQUE
# ======================================================
st.subheader("Evolution des points")
st.line_chart(j_matchs.set_index("GAME_DATE")["PTS"])

st.divider()

# ======================================================
# ANALYSE DU PARI
# ======================================================
st.subheader("Analyse du pari")

marche = st.selectbox(
    "Marche",
    ["PTS", "PRA", "AST", "REB"]
)

ligne_prop = props[
    (props["PLAYER_NAME"] == joueur) &
    (props["STAT"] == marche)
].iloc[0]

ligne_book = st.number_input(
    "Ligne bookmaker",
    value=float(round(ligne_prop["MEAN"], 1))
)

moyenne_ajustee = ligne_prop["MEAN"] * coef_def
ecart_type = ligne_prop["STD"]

if pd.isna(ecart_type) or ecart_type == 0:
    ecart_type = 1

proba_over = 1 - norm.cdf(ligne_book, moyenne_ajustee, ecart_type)
value = abs(proba_over - 0.5)

st.write("Moyenne ajustee :", round(moyenne_ajustee, 2))
st.write("Probabilite Over :", round(proba_over * 100, 1), "%")
st.write("Value estimee :", round(value * 100, 1), "%")

st.divider()

# ======================================================
# DECISION DU MODELE
# ======================================================
st.subheader("Decision du modele")

if proba_over >= 0.65:
    st.success("OVER fortement recommande")
elif proba_over <= 0.35:
    st.error("UNDER fortement recommande")
else:
    st.warning("Aucune value claire")

st.divider()

# ======================================================
# GESTION DE BANKROLL
# ======================================================
st.subheader("Gestion de bankroll")

bankroll = st.number_input(
    "Bankroll totale",
    value=500.0
)

mise_recommandee = bankroll * 0.02
st.write("Mise recommandee (2 %) :", round(mise_recommandee, 2))

st.divider()

# ======================================================
# AVERTISSEMENT
# ======================================================
st.write(
    "Avertissement : ce tableau de bord est un outil d'aide a la decision. "
    "Il ne garantit aucun gain. Pariez de maniere responsable."
)
