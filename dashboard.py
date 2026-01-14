import streamlit as st
import pandas as pd
from scipy.stats import norm
from pathlib import Path

# ================= CONFIG =================
st.set_page_config(
    page_title="Dashboard Paris NBA — PRA (manuel)",
    layout="wide"
)

DATA_PARIS = Path("data/paris.csv")
DATA_PARIS.parent.mkdir(exist_ok=True)

# ================= CHARGEMENT DONNÉES =================
games = pd.read_csv("data/players_7_games.csv")
agg = pd.read_csv("data/players_aggregated.csv")

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
st.title("🏀 Dashboard Paris NBA — PRA (manuel)")

player = st.selectbox(
    "👤 Joueur",
    sorted(agg["PLAYER_NAME"].unique())
)

p_games = games[games["PLAYER_NAME"] == player].copy()

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
prob_over = 1 - norm.cdf(ligne, pra_modele, std)
prob_over = round(prob_over, 3)

proba_cote = 1 / cote
value = prob_over - proba_cote

# Kelly light 25 %
edge = prob_over * (cote - 1) - (1 - prob_over)
mise = 0
if edge > 0:
    kelly_full = edge / (cote - 1)
    mise = round(100 * kelly_full * 0.25, 2)  # bankroll = 100 €

# ================= DÉCISION =================
decision = "NO BET"

if prob_over >= 0.62 and value >= 0.05 and mise > 0:
    decision = "OVER"

# ================= AFFICHAGE =================
st.divider()
st.subheader("📌 Décision du modèle")

c1, c2, c3, c4 = st.columns(4)

c1.metric("📊 PRA modèle (7 matchs)", pra_modele)
c2.metric("📈 Probabilité Over", f"{round(prob_over*100,1)} %")
c3.metric("🎯 Proba implicite cote", f"{round(proba_cote*100,1)} %")
c4.metric("💎 Value", f"{round(value*100,1)} %")

if decision == "OVER":
    st.success(f"✅ OVER PRA — Mise conseillée : {mise} €")
else:
    st.error("❌ NO BET — Value insuffisante")

# ================= ENREGISTRER PARI =================
st.divider()
st.subheader("💰 Enregistrer le pari")

if decision == "OVER":
    with st.form("form_pari"):
        mise_user = st.number_input("Mise jouée (€)", 1.0, 500.0, float(mise))
        submit = st.form_submit_button("📥 Enregistrer")

    if submit:
        new_row = {
            "DATE": pd.Timestamp.today().date(),
            "JOUEUR": player,
            "TYPE": "OVER PRA",
            "LIGNE": ligne,
            "COTE": cote,
            "MISE": mise_user,
            "RESULTAT": "EN ATTENTE",
            "PROFIT": 0
        }
        paris = pd.concat([paris, pd.DataFrame([new_row])])
        paris.to_csv(DATA_PARIS, index=False)
        st.success("Pari enregistré ✔️")
else:
    st.info("Pari désactivé")

# ================= HISTORIQUE =================
st.divider()
st.subheader("📒 Historique des paris")

if paris.empty:
    st.info("Aucun pari enregistré.")
else:
    editable = st.data_editor(
        paris,
        use_container_width=True,
        column_config={
            "RESULTAT": st.column_config.SelectboxColumn(
                "Résultat",
                options=["EN ATTENTE", "GAGNÉ", "PERDU"]
            )
        }
    )

    def calc_profit(row):
        if row["RESULTAT"] == "GAGNÉ":
            return round(row["MISE"] * (row["COTE"] - 1), 2)
        if row["RESULTAT"] == "PERDU":
            return -row["MISE"]
        return 0

    editable["PROFIT"] = editable.apply(calc_profit, axis=1)
    editable.to_csv(DATA_PARIS, index=False)

    total_mise = editable["MISE"].sum()
    total_profit = editable["PROFIT"].sum()
    roi = (total_profit / total_mise * 100) if total_mise > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("📌 Paris", len(editable))
    c2.metric("💰 Profit net", f"{total_profit:.2f} €")
    c3.metric("📊 ROI", f"{roi:.1f} %")