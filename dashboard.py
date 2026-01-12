import streamlit as st
import pandas as pd
from scipy.stats import norm

from analysis.b2b import is_back_to_back
from analysis.odds import fetch_winamax_pra
from analysis.alerts import send_alert
from analysis.explain import explain
from analysis.roi import load_roi

# ================= CONFIG =================
st.set_page_config(
    page_title="Dashboard Paris NBA — PRA",
    page_icon="🏀",
    layout="wide"
)

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

player = st.selectbox("👤 Joueur", sorted(agg["PLAYER_NAME"].unique()))
p_games = games[games["PLAYER_NAME"] == player]

latest = p_games.sort_values("GAME_DATE").iloc[-1]
matchup = latest["MATCHUP"]
team_abbr = matchup.split(" ")[0]
home = "vs" in matchup
b2b = is_back_to_back(team_abbr)

row = props[(props["PLAYER_NAME"] == player) & (props["STAT"] == "PRA")].iloc[0]
model_line = round(row["MEAN"], 1)
std = row["STD"] if row["STD"] > 0 else 1

# --- Winamax SAFE ---
book_line = model_line
odds = 1.90
if not winamax.empty and "PLAYER_NAME" in winamax.columns:
    wm = winamax[winamax["PLAYER_NAME"].str.lower() == player.lower()]
    if not wm.empty:
        wm = wm.iloc[0]
        book_line = wm["LINE"]
        odds = wm["ODDS"]

# ================= MODEL =================
prob = 1 - norm.cdf(book_line, model_line, std)
value = abs(prob - 0.5)
p90 = p_games["PRA"].quantile(0.9)

if prob >= 0.62 and value >= 0.15 and p90 <= book_line + 6:
    decision = "OVER A"
elif prob >= 0.58 and value >= 0.12:
    decision = "OVER B"
else:
    decision = "NO BET"

# ================= DISPLAY =================
st.divider()
st.subheader("📌 Décision du modèle")

if decision == "OVER A":
    st.success("🟢 OVER PRA — CONFIANCE A")
    send_alert(
        BOT_TOKEN, CHAT_ID,
        player, matchup, home, b2b,
        model_line, book_line, odds, prob
    )
elif decision == "OVER B":
    st.warning("🟡 OVER PRA — CONFIANCE B")
else:
    st.error("❌ NO BET")

# --- KPIs ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("📊 PRA modèle", model_line)
c2.metric("🎯 Ligne Book", f"{book_line} @ {odds}")
c3.metric("📈 Proba Over", f"{round(prob*100,1)} %")
c4.metric("🏠 / 🔁", f"{'Home' if home else 'Away'} | {'B2B' if b2b else 'Rest'}")

# --- Explanation ---
st.info(explain(decision, prob, value, p90, book_line))

# --- ROI ---
st.divider()
st.subheader("🏆 Classement joueurs rentables (ROI réel)")

roi = load_roi()
if roi.empty:
    st.info("Pas encore assez de paris validés")
else:
    st.dataframe(roi.head(10), use_container_width=True)
