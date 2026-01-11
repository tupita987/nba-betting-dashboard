import streamlit as st
import pandas as pd
import requests

BOT_TOKEN = "8414100374:AAGV1DBabq1w8JYzYEltG
-vuG2P10K4mNcc"
CHAT_ID = "6139600150"

def send_alert(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except:
        pass
from scipy.stats import norm

from analysis.b2b import is_back_to_back

# ======================================================
# MAPPING OFFICIEL NBA
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
# CONFIG
# ======================================================
st.set_page_config(page_title="Dashboard Paris NBA", layout="wide")

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
defense["COEF_DEF"] = defense["DEF_RATING"] / defense["DEF_RATING"].mean()

# ======================================================
# UI
# ======================================================
st.title("Tableau de bord Paris NBA")
st.write("PRA • OVER uniquement • alertes automatiques")

st.divider()

player = st.selectbox("Choisir un joueur", sorted(agg["PLAYER_NAME"].unique()))
p_row = agg[agg["PLAYER_NAME"] == player].iloc[0]
p_games = games[games["PLAYER_NAME"] == player]

# ======================================================
# CONTEXTE VIA MATCHUP
# ======================================================
latest_game = p_games.sort_values("GAME_DATE").iloc[-1]
matchup = latest_game["MATCHUP"]

team_abbr = matchup.split(" ")[0]
team_full = TEAM_MAP.get(team_abbr, team_abbr)

home = "vs" in matchup
coef_home = 1.05 if home else 0.97

try:
    b2b = is_back_to_back(team_abbr)
except:
    b2b = False

coef_fatigue = 0.96 if b2b else 1.0

opponent = st.selectbox("Equipe adverse", sorted(defense["TEAM"].unique()))
coef_def = defense.loc[defense["TEAM"] == opponent, "COEF_DEF"].values[0]
coef_def = min(max(coef_def, 0.92), 1.08)

# ======================================================
# CONTEXTE
# ======================================================
c1, c2, c3 = st.columns(3)
c1.metric("Equipe", team_full)
c2.metric("Domicile", "Oui" if home else "Non")
c3.metric("Back-to-back", "Oui" if b2b else "Non")

st.divider()

# ======================================================
# STATS
# ======================================================
c1, c2, c3, c4 = st.columns(4)
c1.metric("PTS", round(p_row["PTS_AVG"], 1))
c2.metric("REB", round(p_row["REB_AVG"], 1))
c3.metric("AST", round(p_row["AST_AVG"], 1))
c4.metric("PRA", round(p_row["PRA_AVG"], 1))

# ======================================================
# ANALYSE PRA
# ======================================================
row = props[(props["PLAYER_NAME"] == player) & (props["STAT"] == "PRA")].iloc[0]
line = st.number_input("Ligne bookmaker PRA", value=float(round(row["MEAN"], 1)))

mean_adj = row["MEAN"] * coef_def * coef_home * coef_fatigue
std = row["STD"] if row["STD"] > 0 else 1

prob_over = 1 - norm.cdf(line, mean_adj, std)
value = abs(prob_over - 0.5)
p90 = p_games["PRA"].quantile(0.9)

st.write("Probabilité Over :", round(prob_over * 100, 1), "%")
st.write("Value estimée :", round(value * 100, 1), "%")
st.write("P90 PRA :", round(p90, 1))

# ======================================================
# DECISION
# ======================================================
decision = "NO BET"

if prob_over >= 0.57 and value >= 0.12 and p90 <= line + 8:
    decision = "OVER"

# ======================================================
# MISE
# ======================================================
bankroll = st.number_input("Bankroll", value=500.0)
stake = bankroll * (0.03 if prob_over >= 0.62 else 0.015) if decision == "OVER" else 0

# ======================================================
# ALERTES TELEGRAM (ANTI-SPAM)
# ======================================================
alert_key = f"{player}_{line}_{round(prob_over,2)}"

if "sent_alerts" not in st.session_state:
    st.session_state["sent_alerts"] = set()

if decision == "OVER":
    st.success("PARI AUTORISÉ : OVER PRA")
    st.write("Mise recommandée :", round(stake, 2))

    if alert_key not in st.session_state["sent_alerts"]:
        message = f"""
🔥 <b>OVER PRA VALIDÉ</b>

👤 {player}
🏀 {team_full}
📏 Ligne : {line}
📈 Proba : {round(prob_over*100,1)} %

🏠 Domicile : {'Oui' if home else 'Non'}
🔁 B2B : {'Oui' if b2b else 'Non'}
💰 Mise : {round(stake,2)}
"""
        send_alert(message)
        st.session_state["sent_alerts"].add(alert_key)
else:
    st.warning("NO BET")

st.divider()
st.write("Outil d’aide à la décision — discipline obligatoire.")