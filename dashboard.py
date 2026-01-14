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
defense = pd.read_csv("data/defense_teams.csv")

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
        "DATE", "JOUEUR", "TYPE", "LIGNE",
        "COTE", "MISE", "RESULTAT", "PROFIT"
    ])

# ================= UI =================
st.title("🏀 Dashboard Paris NBA — PRA")
st.caption("Forme récente + ligne Winamax + défense adverse")

player = st.selectbox(
    "👤 Joueur",
    sorted(games["PLAYER_NAME"].unique())
)

p_games = games[games["PLAYER_NAME"] == player].copy()

# ================= PRA MODÈLE =================
pra_modele = (
    p_games.sort_values("GAME_DATE")
    .tail(7)["PRA"]
    .mean()
)
pra_modele = round(pra_modele, 1)

# ================= MATCHUP & ÉQUIPE ADVERSE =================
matchup = p_games.sort_values("GAME_DATE").iloc[-1].get("MATCHUP", "")

team_player = None
team_opp = None
home = False

if isinstance(matchup, str):
    if " vs " in matchup:
        team_player, team_opp = matchup.split(" vs ")
        home = True
    elif " @ " in matchup:
        team_player, team_opp = matchup.split(" @ ")
        home = False

if team_opp is None:
    team_opp = "UNKNOWN"

# ================= DÉFENSE ADVERSE =================
row_def = defense[defense["TEAM"] == team_opp]

if not row_def.empty:
    def_label = row_def.iloc[0]["DEF_LABEL"]
else:
    def_label = "AVERAGE_DEF"

# Modificateur défense
def_mod = {
    "STRONG_DEF": -0.04,
    "AVERAGE_DEF": 0.0,
    "WEAK_DEF": +0.05
}.get(def_label, 0.0)

# ================= LIGNE WINAMAX (MANUELLE) =================
st.divider()
st.subheader("🎯 Ligne Winamax (entrée manuelle)")

c1, c2 = st.columns(2)
ligne = c1.number_input(
    "Ligne PRA",
    min_value=0.0,
    step=0.5,
    value=0.0
)
cote = c2.number_input(
    "Cote",
    min_value=1.01,
    step=0.01,
    value=1.90
)

ligne_disponible = ligne > 0

# ================= PROBABILITÉS =================
std = p_games["PRA"].std()
if pd.isna(std) or std < 1:
    std = 5

prob_brute = 1 - norm.cdf(ligne, pra_modele, std)
prob_adj = min(max(prob_brute + def_mod, 0), 1)

value = prob_adj - (1 / cote)

# ================= KELLY LIGHT 25% =================
kelly = (
    ((prob_adj * cote) - 1) / (cote - 1)
    if value > 0 else 0
)
kelly = max(round(kelly * 0.25, 2), 0)

# ================= DÉCISION =================
if not ligne_disponible:
    decision = "NO BET"
    reason = "Ligne Winamax non renseignée"
elif prob_adj >= 0.62 and value >= 0.04:
    decision = "OVER"
    reason = "Value forte détectée"
elif prob_adj >= 0.55 and value >= 0.02:
    decision = "WATCH"
    reason = "Value moyenne"
else:
    decision = "NO BET"
    reason = "Avantage insuffisant"

# ================= AFFICHAGE =================
st.divider()
st.subheader("📌 Décision du modèle")

if decision == "OVER":
    st.success("🟢 OVER PRA — PARI AUTORISÉ")
elif decision == "WATCH":
    st.warning("🟠 À SURVEILLER")
else:
    st.error("🔴 NO BET")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("📊 PRA modèle", pra_modele)
c2.metric("🎯 Ligne Winamax", f"{ligne} @ {cote}")
c3.metric("📈 Proba brute", f"{round(prob_brute*100,1)} %")
c4.metric("🛡️ Défense adverse", def_label)
c5.metric("📈 Proba ajustée", f"{round(prob_adj*100,1)} %")

st.info(
    f"💎 Value : {round(value*100,1)} % | "
    f"💰 Mise Kelly (25%) : {kelly}"
)

# ================= PARIER =================
st.divider()
st.subheader("💰 Parier")

if decision == "OVER":
    with st.form("form_pari"):
        mise = st.number_input(
            "Mise (€)",
            min_value=1.0,
            max_value=1000.0,
            value=max(10.0, kelly * 100),
            step=1.0
        )
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
    st.info(reason)

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