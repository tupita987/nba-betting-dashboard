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

BANKROLL = 100  # bankroll de référence €

# ================= CHARGEMENT DONNÉES =================
games = pd.read_csv("data/players_7_games.csv")
defense = pd.read_csv("data/team_defense.csv")

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
        "DATE", "JOUEUR", "TYPE",
        "LIGNE", "COTE",
        "MISE", "RESULTAT", "PROFIT"
    ])

# ================= UI =================
st.title("🏀 Dashboard Paris NBA — PRA")
st.caption("Forme récente • Ligne Winamax • Défense adverse • Seuils dynamiques")

player = st.selectbox(
    "👤 Joueur",
    sorted(games["PLAYER_NAME"].unique())
)

p_games = games[games["PLAYER_NAME"] == player].copy()

# ================= PRA MODÈLE =================
pra_modele = round(
    p_games.sort_values("GAME_DATE")
    .tail(7)["PRA"].mean(),
    1
)

# ================= MATCHUP =================
matchup = p_games.sort_values("GAME_DATE").iloc[-1].get("MATCHUP", "")

team_opp = "UNKNOWN"
home = False

if isinstance(matchup, str):
    if " vs " in matchup:
        _, team_opp = matchup.split(" vs ")
        home = True
    elif " @ " in matchup:
        _, team_opp = matchup.split(" @ ")
        home = False

team_opp = team_opp.strip()

# ================= DÉFENSE ADVERSE =================
row_def = defense[defense["TEAM"] == team_opp]

def_label = "AVERAGE_DEF"

if not row_def.empty:
    def_label = row_def.iloc[0]["DEF_LABEL"]

# ================= SEUILS DYNAMIQUES =================
if def_label == "WEAK_DEF":
    seuil_jaune = 0.60
    seuil_vert = 0.65
elif def_label == "STRONG_DEF":
    seuil_jaune = 0.64
    seuil_vert = 0.69
else:  # AVERAGE_DEF
    seuil_jaune = 0.62
    seuil_vert = 0.67

# ================= SAISIE WINAMAX =================
st.divider()
st.subheader("🎯 Ligne Winamax (saisie manuelle)")

c1, c2 = st.columns(2)

ligne = c1.number_input(
    "Ligne PRA",
    min_value=0.0,
    step=0.5,
    value=0.0
)

cote = c2.number_input(
    "Cote Over",
    min_value=1.01,
    step=0.01,
    value=1.90
)

ligne_ok = ligne > 0

# ================= CALCUL PROBABILITÉS =================
std = p_games["PRA"].std()
if pd.isna(std) or std < 1:
    std = 5

prob_over = 1 - norm.cdf(ligne, pra_modele, std)
prob_over = max(min(prob_over, 0.99), 0.01)

proba_cote = 1 / cote
value = prob_over - proba_cote

# ================= FEU TRICOLORE =================
if not ligne_ok:
    couleur = "ROUGE"
    decision = "NO BET"
    reason = "Ligne Winamax non renseignée"

elif prob_over < seuil_jaune:
    couleur = "ROUGE"
    decision = "NO BET"
    reason = "Probabilité insuffisante"

elif seuil_jaune <= prob_over < seuil_vert:
    couleur = "JAUNE"
    decision = "WATCH"
    reason = "Edge détecté mais marge insuffisante"

elif prob_over >= seuil_vert and value >= 0.05:
    couleur = "VERT"
    decision = "OVER"
    reason = "Value confirmée + seuil défense OK"

else:
    couleur = "ROUGE"
    decision = "NO BET"
    reason = "Pas de value malgré proba élevée"

# ================= KELLY LIGHT (25%) =================
kelly = 0
if couleur == "VERT":
    k = ((prob_over * cote) - 1) / (cote - 1)
    kelly = round(max(k, 0) * BANKROLL * 0.25, 2)

# ================= AFFICHAGE =================
st.divider()
st.subheader("📌 Décision du modèle")

if couleur == "VERT":
    st.success("🟢 PARI AUTORISÉ — OVER PRA")
elif couleur == "JAUNE":
    st.warning("🟡 EDGE LÉGER — À SURVEILLER")
else:
    st.error("🔴 NO BET")

st.caption(
    f"🚦 Seuils défense {def_label} — "
    f"🟡 {int(seuil_jaune*100)} % | "
    f"🟢 {int(seuil_vert*100)} %"
)

c1, c2, c3, c4, c5, c6 = st.columns(6)

c1.metric("📊 PRA modèle", pra_modele)
c2.metric("🎯 Ligne Winamax", f"{ligne} @ {cote}")
c3.metric("📈 Probabilité", f"{round(prob_over*100,1)} %")
c4.metric("🛡️ Défense adverse", def_label)
c5.metric("💎 Value", f"{round(value*100,1)} %")
c6.metric("💰 Mise Kelly", f"{kelly} €")

# ================= ENREGISTRER PARI =================
st.divider()
st.subheader("💰 Enregistrer le pari")

if couleur == "VERT":
    with st.form("form_pari"):
        mise = st.number_input(
            "Mise (€)",
            min_value=1.0,
            max_value=1000.0,
            value=max(10.0, kelly),
            step=1.0
        )
        submit = st.form_submit_button("📥 Enregistrer")

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