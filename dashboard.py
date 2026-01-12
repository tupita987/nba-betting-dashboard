import streamlit as st
import pandas as pd
import requests
from scipy.stats import norm
from datetime import datetime
from pathlib import Path

from analysis.b2b import is_back_to_back
from analysis.odds import fetch_winamax_pra

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(page_title="Dashboard Paris NBA", layout="wide")

BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
ODDS_KEY = st.secrets.get("THEODDS_API_KEY")

def send_alert(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
    except:
        pass

# ======================================================
# LOAD DATA
# ======================================================
@st.cache_data(ttl=3600)
def load_all():
    games = pd.read_parquet("data_export/games.parquet")
    agg = pd.read_parquet("data_export/agg.parquet")
    defense = pd.read_parquet("data_export/defense.parquet")
    props = pd.read_parquet("data_export/props.parquet")
    return games, agg, defense, props

games, agg, defense, props = load_all()
games["PRA"] = games["PTS"] + games["REB"] + games["AST"]

@st.cache_data(ttl=300)
def load_winamax():
    if not ODDS_KEY:
        return pd.DataFrame()
    return fetch_winamax_pra(ODDS_KEY)

winamax = load_winamax()
st.write("DEBUG winamax columns:", list(winamax.columns))
st.write("DEBUG winamax preview:", winamax.head())

# ======================================================
# LOG
# ======================================================
LOG = Path("data/decisions.csv")
LOG.parent.mkdir(exist_ok=True)
if not LOG.exists():
    pd.DataFrame(columns=[
        "date","player","line","odds","stake",
        "prob","decision","result","profit"
    ]).to_csv(LOG, index=False)

# ======================================================
# UI
# ======================================================
st.title("🏀 Dashboard Paris NBA — PRA + Winamax")

player = st.selectbox("Joueur", sorted(agg["PLAYER_NAME"].unique()))
p_row = agg[agg["PLAYER_NAME"] == player].iloc[0]
p_games = games[games["PLAYER_NAME"] == player]

latest = p_games.sort_values("GAME_DATE").iloc[-1]
team_abbr = latest["MATCHUP"].split(" ")[0]
home = "vs" in latest["MATCHUP"]
b2b = is_back_to_back(team_abbr)

row = props[(props["PLAYER_NAME"] == player) & (props["STAT"] == "PRA")].iloc[0]
line_model = float(round(row["MEAN"], 1))
std = row["STD"] if row["STD"] > 0 else 1

# Winamax
wm = winamax[winamax["PLAYER_NAME"].str.lower() == player.lower()]
if not wm.empty:
    wm = wm.iloc[0]
    line_book = wm["LINE"]
    odds_book = wm["ODDS"]
else:
    line_book = line_model
    odds_book = 1.90

prob = 1 - norm.cdf(line_book, line_model, std)
value = abs(prob - 0.5)
p90 = p_games["PRA"].quantile(0.9)

decision = "OVER" if prob >= 0.57 and value >= 0.12 and p90 <= line_book + 8 else "NO BET"

# ======================================================
# DECISION
# ======================================================
st.divider()
st.subheader("Décision du modèle")

if decision == "OVER":
    st.success("✅ OVER PRA AUTORISÉ")
else:
    st.warning("❌ NO BET")

st.write(f"📊 PRA moyen modèle : {line_model}")
st.write(f"📈 Ligne Winamax : {line_book} | Cote : {odds_book}")
st.write(f"🎯 Probabilité Over : {round(prob*100,1)} %")
st.write(f"🏠 Domicile : {'Oui' if home else 'Non'} | 🔁 B2B : {'Oui' if b2b else 'Non'}")

# ======================================================
# ENREGISTRER
# ======================================================
stake = st.number_input("Mise (€)", value=10.0)

if st.button("Enregistrer le pari"):
    df = pd.read_csv(LOG)
    df.loc[len(df)] = [
        datetime.utcnow().strftime("%Y-%m-%d"),
        player, line_book, odds_book,
        stake, round(prob,4),
        decision, "PENDING", 0
    ]
    df.to_csv(LOG, index=False)

    if decision == "OVER":
        send_alert(f"OVER PRA\n{player}\nLigne {line_book} @ {odds_book}")

    st.success("Pari enregistré")

# ======================================================
# ROI / CLASSEMENT
# ======================================================
st.divider()
st.subheader("Classement joueurs rentables (ROI réel)")

df = pd.read_csv(LOG)
done = df[df["result"].isin(["WIN","LOSS"])]

if len(done) >= 3:
    rank = done.groupby("player").agg(
        PARIS=("profit","count"),
        PROFIT=("profit","sum"),
        MISE=("stake","sum")
    ).reset_index()
    rank["ROI_%"] = (rank["PROFIT"]/rank["MISE"])*100
    rank = rank.sort_values("ROI_%", ascending=False)
    st.dataframe(rank, use_container_width=True)
else:
    st.info("Pas encore assez de paris validés")
