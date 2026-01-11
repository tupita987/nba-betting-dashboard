import streamlit as st
import pandas as pd
from scipy.stats import norm

st.set_page_config(page_title="Tableau de bord Paris NBA", layout="wide")

@st.cache_data
def charger_donnees():
    matchs = pd.read_parquet("data_export/games.parquet")
    moyennes = pd.read_parquet("data_export/agg.parquet")
    defenses = pd.read_parquet("data_export/defense.parquet")
    props = pd.read_parquet("data_export/props.parquet")
    return matchs, moyennes, defenses, props

matchs, moyennes, defenses, props = charger_donnees()

defenses["COEF_DEF"] = defenses["DEF_RATING"] / defenses["DEF_RATING"].mean()

st.title("Tableau de bord Paris NBA")
st.write("Analyse des joueurs NBA basee sur les 7 derniers matchs")

joueur = st.selectbox("Choisir un joueur", sorted(moyennes["PLAYER_NAME"].unique()))
j_matchs = matchs[matchs["PLAYER_NAME"] == joueur]
j_moy = moyennes[moyennes["PLAYER_NAME"] == joueur].iloc[0]

st.subheader("Contexte du match")
adversaire = st.selectbox("Equipe adverse", sorted(defenses["TEAM"].unique()))
coef_def = defenses[defenses["TEAM"] == adversaire]["COEF_DEF"].values[0]

st.subheader("Statistiques recentes (7 matchs)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Points", round(j_moy["PTS_AVG"], 1))
c2.metric("Rebonds", round(j_moy["REB_AVG"], 1))
c3.metric("Passes", round(j_moy["AST_AVG"], 1))
c4.metric("PRA", round(j_moy["PRA_AVG"], 1))

st.subheader("Analyse du pari PRA")

row = props[(props["PLAYER_NAME"] == joueur) & (props["STAT"] == "PRA")].iloc[0]

ligne = st.number_input("Ligne bookmaker PRA", value=float(round(row["MEAN"], 1)))

moyenne = row["MEAN"] * coef_def
std = row["STD"] if row["STD"] > 0 else 1

proba = 1 - norm.cdf(ligne, moyenne, std)
value = abs(proba - 0.5)

st.write("Probabilite Over :", round(proba * 100, 1), "%")
st.write("Value estimee :", round(value * 100, 1), "%")

if proba >= 0.57:
    st.success("PARI AUTORISE (strategie validee)")
else:
    st.warning("Pari refuse par la strategie")

bankroll = st.number_input("Bankroll totale", value=500.0)
mise = bankroll * 0.02
st.write("Mise recommandee :", round(mise, 2))

st.write("Outil d'aide a la decision. Aucun gain garanti.")
