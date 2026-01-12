import streamlit as st
import pandas as pd
from scipy.stats import norm

from analysis.b2b import is_back_to_back
from analysis.odds import fetch_winamax_pra
from analysis.alerts import send_alert

# ================= CONFIG =================
st.set_page_config(page_title="Dashboard Paris NBA — PRA", layout="wide")

BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
ODDS_KEY = st.secrets.get("THEODDS_API_KEY")

# ================= DATA =================
@st.cache_data(ttl=3600)
def load_all():
    games = pd.read_parquet("data_export/games.parquet")
    agg = pd.read_parquet("data_export/agg.parquet")
    props = pd.read_parquet("data_export/props.parquet")
    return games, agg, props

games, agg, props = load_all()
games["PRA"] = games["PTS"] + games["REB"] + games["AST"]

@st.cache_data(ttl=300)
def load_winamax():
    if not ODDS_KEY:
        return pd.DataFrame()
    return fetch_winamax_pra(ODDS_KEY)

winamax = load_winamax()

# ================= UI =================
st.title("🏀 Dashboard Paris NBA — PRA")

player = st.selectbox("Joueur", sorted(agg["PLAYER_NAME"].unique()))
p_games = games[games["PLAYER_NAME"] == player]

latest = p_games.sort_values("GAME_DATE").iloc[-1]
team_abbr = latest["MATCHUP"].split(" ")[0]
home = "vs" in latest["MATCHUP"]
b2b = is_back_to_back(team_abbr)

row = props[(props["PLAYER_NAME"] == player) & (props["STAT"] == "PRA")].iloc[0]
line_model = round(row["MEAN"], 1)
std = row["STD"] if row["STD"] > 0 else 1

# Winamax SAFE
line_book = line_model
odds_book = 1.90
if not winamax.empty and "PLAYER_NAME" in winamax.columns:
    wm = winamax[winamax["PLAYER_NAME"].str.lower() == player.lower()]
    if not wm.empty:
        wm = wm.iloc[0]
        line_book = wm["LINE"]
        odds_book = wm["ODDS"]

# ================= MODEL =================
prob = 1 - norm.cdf(line_book, line_model, std)
value = abs(prob - 0.5)
p90 = p_games["PRA"].quantile(0.9)

if prob >= 0.62 and value >= 0.15 and p90 <= line_book + 6:
    decision = "OVER A"
elif prob >= 0.58 and value >= 0.12:
    decision = "OVER B"
else:
    decision = "NO BET"

# ================= DISPLAY =================
st.subheader("Décision du modèle")

if decision == "OVER A":
    st.success("🟢 OVER PRA — CONFIANCE A")
    send_alert(BOT_TOKEN, CHAT_ID, player, line_book, prob, odds_book)
elif decision == "OVER B":
    st.warning("🟡 OVER PRA — CONFIANCE B")
else:
    st.error("❌ NO BET")

st.write(f"PRA modèle : {line_model}")
st.write(f"Ligne Winamax : {line_book} @ {odds_book}")
st.write(f"Probabilité Over : {round(prob*100,1)} %")
st.write(f"Domicile : {'Oui' if home else 'Non'} | B2B : {'Oui' if b2b else 'Non'}")
from analysis.roi import load_roi

st.divider()
st.subheader("Classement joueurs rentables (ROI réel)")

roi = load_roi()
if roi.empty:
    st.info("Pas encore assez de paris validés")
else:
    st.dataframe(roi.head(10))
from analysis.explain import explain

st.subheader("Explication du modèle")
st.info(explain(decision, prob, value, p90, line_book))
