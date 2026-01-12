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

# ================= CHARGEMENT DONNÉES =================
games = pd.read_csv("data/players_7_games.csv")
agg = pd.read_csv("data/players_aggregated.csv")
props = pd.read_csv("data/props_model.csv")

# ================= PRA =================
if "PRA" not in games.columns:
    games["PRA"] = (
        games["PTS"].fillna(0)
        + games["REB"].fillna(0)
        + games["AST"].fillna(0)
    )

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

p_games = games[games["PLAYER_NAME"] == player].copy()

# ================= PRA MODÈLE (7 DERNIERS MATCHS) =================
pra_modele = (
    p_games
    .sort_values("GAME_DATE")
    .tail(7)["PRA"]
    .mean()
)
pra_modele = round(pra_modele, 1)

# ================= LIGNE WINAMAX =================
ligne = None
cote = None

row_prop = props[props["PLAYER_NAME"] == player]

if not row_prop.empty:
    ligne = float(row_prop.iloc[0]["MEAN"])
    cote = float(row_prop.iloc[0].get("ODDS", None))

# ================= PROBABILITÉ (SI LIGNE EXISTE) =================
std = p_games["PRA"].std()
if pd.isna(std) or std < 1:
    std = 5

prob_over = None
if ligne is not None:
    prob_over = round(1 - norm.cdf(ligne, pra_modele, std), 3)

# ================= DÉCISION =================
ligne_disponible = (
    ligne is not None
    and cote is not None
    and ligne > 0
    and cote > 1.01
)

decision = "NO BET"
raison = "⏳ Ligne PRA Winamax non encore publiée"

if ligne_disponible:
    proba_cote = 1 / cote
    marge_value = 0.05

    if prob_over >= 0.62 and prob_over > proba_cote + marge_value:
        decision = "OVER"
        raison = "Value positive détectée"
    else:
        decision = "NO BET"
        raison = "Pas assez de value par rapport à la cote"

# ================= AFFICHAGE =================
st.divider()
st.subheader("📌 Décision du modèle")

if decision == "OVER":
    st.success("✅ PARI AUTORISÉ — OVER PRA")
else:
    st.error("❌ NO BET")

c1, c2, c3, c4 = st.columns(4)

c1.metric("📊 PRA modèle (7 matchs)", pra_modele)

if ligne_disponible:
    c2.metric("🎯 Ligne Winamax", f"{ligne} @ {cote}")
    c3.metric("📈 Probabilité Over", f"{round(prob_over*100,1)} %")
    c4.metric("📉 Value", f"{round((prob_over - (1/cote))*100,1)} %")
else:
    c2.metric("🎯 Ligne Winamax", "Non publiée")
    c3.metric("📈 Probabilité Over", "—")
    c4.metric("📉 Value", "—")

st.info(raison)

# ================= PARIER (UNIQUEMENT SI OVER) =================
st.divider()
st.subheader("💰 Parier")

if decision == "OVER":
    with st.form("form_pari"):
        mise = st.number_input("Mise (€)", 1.0, 500.0, 10.0, step=1.0)
        submit = st.form_submit_button("📥 Enregistrer le pari")

    if submit:
        new_row = {
            "DATE": pd.Timestamp.today().date(),
            "JOUEUR": player,
            "TYPE": "OVER PRA",
            "LIGNE": ligne,
            "COTE": cote,
            "MISE": mise,
            "RESULTAT": "EN ATTENTE",
            "PROFIT": 0
        }
        paris = pd.concat([paris, pd.DataFrame([new_row])])
        paris.to_csv(DATA_PARIS, index=False)
        st.success("Pari enregistré ✔️")
else:
    st.info("Pari désactivé — marché non disponible ou sans value")

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
