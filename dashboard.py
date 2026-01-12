import streamlit as st
import pandas as pd
import requests
from scipy.stats import norm
from datetime import datetime
from pathlib import Path

from analysis.b2b import is_back_to_back

# ======================================================
# TELEGRAM (SECRETS)
# ======================================================
BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

def send_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, data=payload, timeout=5)

# ======================================================
# NBA TEAM MAP
# ======================================================
TEAM_MAP = {
    "ATL": "Atlanta Hawks", "BOS": "Boston Celtics", "BKN": "Brooklyn Nets",
    "CHA": "Charlotte Hornets", "CHI": "Chicago Bulls", "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks", "DEN": "Denver Nuggets", "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors", "HOU": "Houston Rockets", "IND": "Indiana Pacers",
    "LAC": "Los Angeles Clippers", "LAL": "Los Angeles Lakers",
    "MEM": "Memphis Grizzlies", "MIA": "Miami Heat", "MIL": "Milwaukee Bucks",
    "MIN": "Minnesota Timberwolves", "NOP": "New Orleans Pelicans",
    "NYK": "New York Knicks", "OKC": "Oklahoma City Thunder", "ORL": "Orlando Magic",
    "PHI": "Philadelphia 76ers", "PHX": "Phoenix Suns",
    "POR": "Portland Trail Blazers", "SAC": "Sacramento Kings",
    "SAS": "San Antonio Spurs", "TOR": "Toronto Raptors",
    "UTA": "Utah Jazz", "WAS": "Washington Wizards"
}

# ======================================================
# DECISION LOGGER (AXE 5)
# ======================================================
LOG_PATH = Path("data/decisions.csv")
LOG_PATH.parent.mkdir(exist_ok=True)

if not LOG_PATH.exists():
    pd.DataFrame(columns=[
        "date", "player", "team", "line",
        "prob_over", "decision"
    ]).to_csv(LOG_PATH, index=False)

def log_decision(player, team, line, prob, decision):
    df = pd.read_csv(LOG_PATH)
    df.loc[len(df)] = [
        datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        player, team, line, round(prob, 4), decision
    ]
    df.to_csv(LOG_PATH, index=False)

# ======================================================
# CONFIG
# ======================================================
st.set_page_config(page_title="Dashboard Paris NBA", layout="wide")

@st.cache_data(ttl=3600)
def load_all():
    return (
        pd.read_parquet("data_export/games.parquet"),
        pd.read_parquet("data_export/agg.parquet"),
        pd.read_parquet("data_export/defense.parquet"),
        pd.read_parquet("data_export/props.parquet"),
    )

games, agg, defense, props = load_all()
games["PRA"] = games["PTS"] + games["REB"] + games["AST"]

# ======================================================
# SELECTION
# ======================================================
player = st.selectbox("Choisir un joueur", sorted(agg["PLAYER_NAME"].unique()))
p_row = agg[agg["PLAYER_NAME"] == player].iloc[0]
p_games = games[games["PLAYER_NAME"] == player]

latest_game = p_games.sort_values("GAME_DATE").iloc[-1]
matchup = latest_game["MATCHUP"]

team_abbr = matchup.split(" ")[0]
team_full = TEAM_MAP.get(team_abbr, team_abbr)
home = "vs" in matchup

try:
    b2b = is_back_to_back(team_abbr)
except:
    b2b = False

opponent = st.selectbox("Equipe adverse", sorted(defense["TEAM"].unique()))
coef_def = defense.loc[defense["TEAM"] == opponent, "DEF_RATING"].values[0] / defense["DEF_RATING"].mean()

# ======================================================
# PRA ANALYSIS
# ======================================================
row = props[(props["PLAYER_NAME"] == player) & (props["STAT"] == "PRA")].iloc[0]
line = st.number_input("Ligne bookmaker PRA", value=float(round(row["MEAN"], 1)))

mean = row["MEAN"] * (1.05 if home else 0.97) * (0.96 if b2b else 1.0) * coef_def
std = row["STD"] if row["STD"] > 0 else 1

prob_over = 1 - norm.cdf(line, mean, std)
p90 = p_games["PRA"].quantile(0.9)
value = abs(prob_over - 0.5)

decision = "NO BET"
if prob_over >= 0.57 and value >= 0.12 and p90 <= line + 8:
    decision = "OVER"

# ======================================================
# AXE 1 — DECISION EN HAUT
# ======================================================
st.divider()
if decision == "OVER":
    st.success(f"✅ PARI AUTORISÉ — OVER PRA ({team_full})")
else:
    st.error("❌ NO BET — Aucune value détectée")

st.write(f"Probabilité Over : {round(prob_over*100,1)} %")

# ======================================================
# LOG + ALERTE
# ======================================================
log_decision(player, team_full, line, prob_over, decision)

alert_key = f"{player}_{line}"
if "alerts" not in st.session_state:
    st.session_state["alerts"] = set()

if decision == "OVER" and alert_key not in st.session_state["alerts"]:
    send_alert(
        f"OVER PRA\n{player}\n{team_full}\nLigne {line}\nProba {round(prob_over*100,1)}%"
    )
    st.session_state["alerts"].add(alert_key)

# ======================================================
# HISTORIQUE (AXE 5)
# ======================================================
st.divider()
st.subheader("Historique des décisions")

history = pd.read_csv(LOG_PATH)
st.dataframe(history.tail(50), use_container_width=True)
# ======================================================
# CLASSEMENT DES JOUEURS (EDGE THEORIQUE)
# ======================================================
st.divider()
st.subheader("Classement des joueurs les plus rentables (théorique)")

history = pd.read_csv(LOG_PATH)

# On ne garde que les OVER
over_only = history[history["decision"] == "OVER"].copy()

if len(over_only) < 5:
    st.info("Pas encore assez de données pour établir un classement.")
else:
    ranking = (
        over_only
        .groupby("player")
        .agg(
            NB_OVER=("decision", "count"),
            PROBA_MOY=("prob_over", "mean"),
        )
        .reset_index()
    )

    ranking["EDGE_MOY"] = ranking["PROBA_MOY"] - 0.5
    ranking = ranking.sort_values("EDGE_MOY", ascending=False)

    st.dataframe(
        ranking,
        use_container_width=True
    )
