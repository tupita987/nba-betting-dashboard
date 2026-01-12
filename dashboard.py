import streamlit as st
import pandas as pd
import requests
from scipy.stats import norm
from datetime import datetime
from pathlib import Path

from analysis.b2b import is_back_to_back

# ======================================================
# CONFIG STREAMLIT
# ======================================================
st.set_page_config(page_title="Dashboard Paris NBA", layout="wide")

# ======================================================
# TELEGRAM (SECRETS STREAMLIT)
# ======================================================
BOT_TOKEN = st.secrets["TELEGRAM_BOT_TOKEN"]
CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]

def send_alert(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload, timeout=5)
    except:
        pass

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
# DATA LOADER
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

# ======================================================
# DECISION LOG (ROI)
# ======================================================
LOG_PATH = Path("data/decisions.csv")
LOG_PATH.parent.mkdir(exist_ok=True)

if not LOG_PATH.exists():
    pd.DataFrame(columns=[
        "date","player","team","line","odds","stake",
        "prob_over","decision","result","profit"
    ]).to_csv(LOG_PATH, index=False)

def save_log(row):
    df = pd.read_csv(LOG_PATH)
    df.loc[len(df)] = row
    df.to_csv(LOG_PATH, index=False)

# ======================================================
# UI — ANALYSE
# ======================================================
st.title("Dashboard Paris NBA — PRO")

player = st.selectbox("Choisir un joueur", sorted(agg["PLAYER_NAME"].unique()))
p_row = agg[agg["PLAYER_NAME"] == player].iloc[0]
p_games = games[games["PLAYER_NAME"] == player]

latest = p_games.sort_values("GAME_DATE").iloc[-1]
team_abbr = latest["MATCHUP"].split(" ")[0]
team_full = TEAM_MAP.get(team_abbr, team_abbr)

home = "vs" in latest["MATCHUP"]
b2b = is_back_to_back(team_abbr)

row = props[(props["PLAYER_NAME"] == player) & (props["STAT"] == "PRA")].iloc[0]
line = st.number_input("Ligne PRA", value=float(round(row["MEAN"],1)))
odds = st.number_input("Cote bookmaker", value=1.90)

mean = row["MEAN"]
std = row["STD"] if row["STD"] > 0 else 1

prob_over = 1 - norm.cdf(line, mean, std)
value = abs(prob_over - 0.5)
p90 = p_games["PRA"].quantile(0.9)

decision = "OVER" if prob_over >= 0.57 and value >= 0.12 and p90 <= line + 8 else "NO BET"

# ======================================================
# DECISION (AFFICHAGE PROPRE)
# ======================================================
st.divider()
st.subheader("Décision du modèle")

if decision == "OVER":
    st.success(f"✅ PARI AUTORISÉ — OVER PRA ({team_full})")
else:
    st.warning("❌ NO BET — Aucune value détectée")

st.write(f"Probabilité Over : {round(prob_over*100,1)} %")
st.write(f"Domicile : {'Oui' if home else 'Non'} | Back-to-back : {'Oui' if b2b else 'Non'}")

# ======================================================
# ENREGISTRER PARI
# ======================================================
stake = st.number_input("Mise (€)", value=10.0)

if st.button("Enregistrer le pari"):
    save_log([
        datetime.utcnow().strftime("%Y-%m-%d"),
        player, team_full, line, odds, stake,
        round(prob_over,4), decision, "PENDING", 0
    ])
    if decision == "OVER":
        send_alert(f"OVER PRA\n{player}\n{team_full}\nLigne {line}")
    st.success("Pari enregistré")

# ======================================================
# SAISIE RESULTATS
# ======================================================
st.divider()
st.subheader("Saisie des résultats")

df = pd.read_csv(LOG_PATH)
pending = df[df["result"] == "PENDING"]

for i, r in pending.iterrows():
    c1, c2, c3 = st.columns(3)
    c1.write(f"{r['player']} — PRA {r['line']}")
    res = c2.selectbox("Résultat", ["WIN","LOSS"], key=f"res{i}")
    if c3.button("Valider", key=f"val{i}"):
        profit = r["stake"]*(r["odds"]-1) if res=="WIN" else -r["stake"]
        df.loc[i,"result"] = res
        df.loc[i,"profit"] = round(profit,2)
        df.to_csv(LOG_PATH, index=False)
        st.experimental_rerun()

# ======================================================
# CLASSEMENT ROI
# ======================================================
st.divider()
st.subheader("Classement des joueurs les plus rentables (ROI réel)")

done = df[df["result"].isin(["WIN","LOSS"])]

if len(done) >= 3:
    ranking = (
        done.groupby("player")
        .agg(
            PARIS=("profit","count"),
            PROFIT=("profit","sum"),
            MISE=("stake","sum")
        )
        .reset_index()
    )
    ranking["ROI_%"] = (ranking["PROFIT"]/ranking["MISE"])*100
    ranking = ranking.sort_values("ROI_%", ascending=False)
    st.dataframe(ranking, use_container_width=True)
else:
    st.info("Pas encore assez de paris terminés")
