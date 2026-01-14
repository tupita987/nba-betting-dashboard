import streamlit as st
import pandas as pd
from scipy.stats import norm
from pathlib import Path

# ================= CONFIG =================
st.set_page_config(
    page_title="Dashboard Paris NBA — PRA",
    layout="wide"
)

BANKROLL = 100
DATA_PARIS = Path("data/paris.csv")
DATA_PARIS.parent.mkdir(exist_ok=True)

# ================= CHARGEMENT DONNÉES =================
games = pd.read_csv("data/players_7_games.csv")
agg = pd.read_csv("data/players_aggregated.csv")
defense = pd.read_csv("data/team_defense.csv")

if "PRA" not in games.columns:
    games["PRA"] = games["PTS"] + games["REB"] + games["AST"]

# ================= HISTORIQUE PARIS =================
if DATA_PARIS.exists():
    paris = pd.read_csv(DATA_PARIS)
else:
    paris = pd.DataFrame(columns=[
        "DATE", "JOUEUR", "TYPE", "LIGNE", "COTE",
        "MISE", "RESULTAT", "PROFIT"
    ])

# ================= UI =================
st.title("🏀 Dashboard Paris NBA — PRA")
st.caption("Forme récente + ligne Winamax + défense adverse")

player = st.selectbox(
    "👤 Joueur",
    sorted(agg["PLAYER_NAME"].unique())
)

p_games = games[games["PLAYER_NAME"] == player].copy()

# ================= MATCHUP =================
last_game = p_games.sort_values("GAME_DATE").iloc[-1]
matchup = last_game["MATCHUP"]

if "vs" in matchup:
    team_player, team_opp = matchup.split(" vs ")
    home = True
else:
    team_player, team_opp = matchup.split(" @ ")
    home = False

team_opp = team_opp.strip()

# ================= PRA MODÈLE =================
pra_modele = (
    p_games
    .sort_values("GAME_DATE")
    .tail(7)["PRA"]
    .mean()
)
pra_modele = round(pra_modele, 1)

std = p_games["PRA"].std()
if pd.isna(std) or std < 1:
    std = 5

# ================= DÉFENSE ADVERSE =================
row_def = defense[defense["TEAM"] == team_opp]

def_bonus = 0.0
def_label = "AVERAGE_DEF"

if not row_def.empty:
    def_label = row_def.iloc[0]["DEF_LABEL"]

    if def_label == "WEAK_DEF":
        def_bonus = 0.03
    elif def_label == "STRONG_DEF":
        def_bonus = -0.03

# ================= SAISIE WINAMAX =================
st.subheader("🎯 Ligne Winamax (saisie manuelle)")

c1, c2 = st.columns(2)

with c1:
    ligne = st.number_input(
        "Ligne PRA Winamax",
        min_value=0.0,
        step=0.5,
        value=round(pra_modele, 1)
    )

with c2:
    cote = st.number_input(
        "Cote Over Winamax",
        min_value=1.01,
        step=0.01,
        value=1.90
    )

# ================= CALCUL =================
prob_brute = 1 - norm.cdf(ligne, pra_modele, std)
prob_adj = max(min(prob_brute + def_bonus, 0.99), 0.01)

proba_cote = 1 / cote
value = prob_adj - proba_cote

edge = prob_adj * (cote - 1) - (1 - prob_adj)
mise_kelly = 0
if edge > 0:
    mise_kelly = round(BANKROLL * (edge / (cote - 1)) * 0.25, 2)

# ================= FEU TRICOLORE =================
decision = "🔴 NO BET"
niveau = "ROUGE"
coef = 0

if prob_adj >= 0.62 and value >= 0.05 and mise_kelly > 0:
    decision = "🟢 PARI FORT"
    niveau = "VERT"
    coef = 1.0
elif prob_adj >= 0.58 and value >= 0.02 and mise_kelly > 0:
    decision = "🟠 PARI JOUABLE"
    niveau = "ORANGE"
    coef = 0.5

mise_conseillee = round(mise_kelly * coef, 2)

# ================= AFFICHAGE =================
st.divider()
st.subheader("📌 Analyse")

c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric("📊 PRA modèle", pra_modele)
c2.metric("📈 Proba brute", f"{round(prob_brute*100,1)} %")
c3.metric("🛡️ Défense adverse", def_label)
c4.metric("📈 Proba ajustée", f"{round(prob_adj*100,1)} %")
c5.metric("💎 Value", f"{round(value*100,1)} %")
c6.metric("💰 Mise Kelly", mise_kelly)

if niveau == "VERT":
    st.success(f"🟢 PARI FORT — Mise conseillée : {mise_conseillee} €")
elif niveau == "ORANGE":
    st.warning(f"🟠 PARI JOUABLE — Mise réduite : {mise_conseillee} €")
else:
    st.error("🔴 NO BET — Avantage insuffisant")