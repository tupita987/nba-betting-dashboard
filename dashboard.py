import streamlit as st
import pandas as pd
from scipy.stats import norm

from analysis.b2b import is_back_to_back
from analysis.odds import fetch_winamax_pra
from analysis.alerts import send_alert, send_combo_alert
from analysis.combine import build_best_combo

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

# ================= UI =================
st.title("🏀 Dashboard Paris NBA — PRA")

# ----------- COMBINÉ INTELLIGENT -----------
st.subheader("🧠 Combiné intelligent du jour")

over_list = []

for _, r in props.iterrows():
    pg = games[games["PLAYER_NAME"] == r["PLAYER_NAME"]]
    if pg.empty:
        continue

    last = pg.sort_values("GAME_DATE").iloc[-1]
    line = round(r["MEAN"], 1)
    std = r["STD"] if r["STD"] > 0 else 1
    prob_i = 1 - norm.cdf(line, r["MEAN"], std)
    value_i = abs(prob_i - 0.5)
    p90_i = pg["PRA"].quantile(0.9)

    if prob_i >= 0.62 and value_i >= 0.15 and p90_i <= line + 6:
        over_list.append({
            "PLAYER_NAME": r["PLAYER_NAME"],
            "MATCHUP": last["MATCHUP"],
            "PROB": prob_i,
            "ODDS": 1.90
        })

over_df = pd.DataFrame(over_list)
combo = build_best_combo(over_df)

if combo:
    st.success("🔥 Combiné intelligent détecté")
    st.write(combo)

    send_combo_alert(BOT_TOKEN, CHAT_ID, combo)
else:
    st.info("Aucun combiné intelligent aujourd’hui")
