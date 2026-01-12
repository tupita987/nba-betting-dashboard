import streamlit as st
import pandas as pd
from scipy.stats import norm
from pathlib import Path

# ================= CONFIG =================
st.set_page_config(
    page_title="Dashboard Paris NBA — PRA",
    layout="wide"
)

DATA_PARIS = Path("data/paris.csv")
DATA_PARIS.parent.mkdir(exist_ok=True)

# ================= CHARGEMENT DATA =================
games = pd.read_csv("data/players_7_games.csv")
agg = pd.read_csv("data/players_aggregated.csv")
props = pd.read_csv("data/props_model.csv")
today = pd.read_csv("data/today_games.csv")

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

player = st.selectbox(
    "👤 Joueur",
    sorted(agg["PLAYER_NAME"].unique())
)

p_row = agg[agg["PLAYER_NAME"] == player].iloc[0]
p_games = games[games["PLAYER_NAME"] == player]

# ===== Calcul PRA si absent =====
if "PRA" not in p_games.columns:
    p_games = p_games.copy()
    p_games["PRA"] = (
        p_games["PTS"].fillna(0) +
        p_games["REB"].fillna(0) +
        p_games["AST"].fillna(0)
    )

pra_mean = round(p_row["PRA_AVG"], 1)
line = round(pra_mean, 1)
odds = 1.9

std = p_games["PRA"].std()
if pd.isna(std) or std == 0:
    std = 5

prob_over = 1 - norm.cdf(line, pra_mean, std)
decision = "OVER" if prob_over >= 0.62 else "NO BET"

# ================= DECISION =================
st.divider()
st.subheader("📌 Décision du modèle")

if decision == "OVER":
    st.success("✅ PARI AUTORISÉ — OVER PRA")
else:
    st.error("❌ NO BET")

c1, c2, c3, c4 = st.columns(4)

c1.metric("📊 PRA modèle", pra_mean)
c2.metric("🎯 Ligne Book", f"{line} @ {odds}")
c3.metric("📈 Proba Over", f"{round(prob_over*100,1)} %")
c4.metric("🏟️ Contexte", "Away | Rest")

st.info("Probabilité trop faible | Pas assez de value | Distribution trop large")

# ================= PARIER =================
st.divider()
st.subheader("💰 Enregistrer un pari")

with st.form("form_pari"):
    mise = st.number_input("Mise (€)", 1.0, 500.0, 10.0, step=1.0)
    type_pari = st.selectbox("Type de pari", ["OVER PRA", "UNDER PRA"])
    submit = st.form_submit_button("📥 Enregistrer le pari")

if submit:
    new_row = {
        "DATE": pd.Timestamp.today().date(),
        "JOUEUR": player,
        "TYPE": type_pari,
        "LIGNE": line,
        "COTE": odds,
        "MISE": mise,
        "RESULTAT": "EN ATTENTE",
        "PROFIT": 0
    }
    paris = pd.concat([paris, pd.DataFrame([new_row])])
    paris.to_csv(DATA_PARIS, index=False)
    st.success("Pari enregistré ✔️")

# ================= HISTORIQUE =================
st.divider()
st.subheader("📒 Historique des paris")

if paris.empty:
    st.info("Aucun pari enregistré pour le moment.")
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

    # Calcul profit
    def calc_profit(row):
        if row["RESULTAT"] == "GAGNÉ":
            return round(row["MISE"] * (row["COTE"] - 1), 2)
        elif row["RESULTAT"] == "PERDU":
            return -row["MISE"]
        return 0

    editable["PROFIT"] = editable.apply(calc_profit, axis=1)
    editable.to_csv(DATA_PARIS, index=False)

    total_mise = editable["MISE"].sum()
    total_profit = editable["PROFIT"].sum()
    roi = (total_profit / total_mise * 100) if total_mise > 0 else 0
    winrate = (editable["RESULTAT"] == "GAGNÉ").mean() * 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📌 Paris", len(editable))
    c2.metric("💸 Mise totale", f"{total_mise:.2f} €")
    c3.metric("💰 Profit net", f"{total_profit:.2f} €")
    c4.metric("📊 ROI", f"{roi:.1f} %")

# ================= CLASSEMENT =================
st.divider()
st.subheader("🏆 Classement joueurs rentables (ROI réel)")

if paris[paris["RESULTAT"] != "EN ATTENTE"].empty:
    st.info("Pas encore assez de paris validés")
else:
    classement = (
        paris[paris["RESULTAT"] != "EN ATTENTE"]
        .groupby("JOUEUR")
        .agg(
            MISE=("MISE", "sum"),
            PROFIT=("PROFIT", "sum")
        )
        .reset_index()
    )
    classement["ROI (%)"] = classement["PROFIT"] / classement["MISE"] * 100
    st.dataframe(
        classement.sort_values("ROI (%)", ascending=False),
        use_container_width=True
    )
