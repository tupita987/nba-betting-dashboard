import streamlit as st
import pandas as pd
from scipy.stats import norm
from analysis.fetch_data_cloud import load_players_games
from analysis.defense_cloud import load_team_defense

@st.cache_data(ttl=3600)
def load_all_data():
    games = load_players_games()
    defense = load_team_defense()
    return games, defense

games, defense = load_all_data()
st.set_page_config(
    page_title="Tableau de bord Paris NBA",
    layout="wide"
)
# --- SAFE DATA CHECK ---
required_cols = ["PLAYER_NAME", "PTS", "REB", "AST", "MIN"]

missing = [c for c in required_cols if c not in games.columns]
if missing:
    st.error(f"Colonnes manquantes dans games: {missing}")
    st.stop()

if games.empty:
    st.error("Aucune donnee joueur chargee depuis l'API NBA")
    st.stop()

# --- PRA ---
games["PRA"] = games["PTS"] + games["REB"] + games["AST"]

# --- AGGREGATION ---
agg = (
    games
    .groupby("PLAYER_NAME")
    .agg(
        PTS_AVG=("PTS", "mean"),
        REB_AVG=("REB", "mean"),
        AST_AVG=("AST", "mean"),
        PRA_AVG=("PRA", "mean"),
        MIN_AVG=("MIN", "mean"),
        GAMES_PLAYED=("PTS", "count")
    )
    .reset_index()
)

# --- DEBUG VISUEL ---
st.write("Apercu donnees joueurs (debug)")
st.write(agg.head())


# Load data
players = pd.read_csv("data/players_aggregated.csv")
trends = pd.read_csv("data/player_trends.csv")
games = pd.read_csv("data/players_7_games.csv")
today = pd.read_csv("data/today_games.csv")
props = pd.read_csv("data/props_model.csv")

st.title("Tableau de bord Paris NBA - Mode Pro")

# --- Match info (safe) ---
st.subheader("Contexte du jour")

if len(today) > 0:
    st.info(
        f"Matchs NBA aujourd'hui : {len(today)} | "
        f"Date : {today['GAME_DATE_EST'].iloc[0]}"
    )
else:
    st.warning("Aucun match NBA detecte aujourd'hui")

# --- Player selection ---
st.subheader("Selection du joueur")

player = st.selectbox(
    "Choisir un joueur",
    sorted(players["PLAYER_NAME"].unique())
)

p_avg = players[players["PLAYER_NAME"] == player]
p_trend = trends[trends["PLAYER_NAME"] == player]
p_games = games[games["PLAYER_NAME"] == player].sort_values("GAME_DATE")

# --- KPIs ---
c1, c2, c3, c4 = st.columns(4)

c1.metric("Points (moyenne)", round(p_avg["PTS_AVG"].values[0], 1))
c2.metric("Minutes (moyenne)", round(p_avg["MIN_AVG"].values[0], 1))
c3.metric("PRA (moyenne)", round(p_avg["PRA_AVG"].values[0], 1))
c4.metric("+/-", round(p_avg["PLUS_MINUS"].values[0], 1))

# --- Trend ---
st.subheader("Forme recente")

if not p_trend.empty and p_trend["HOT"].values[0]:
    st.success("Joueur en forme (HOT)")
elif not p_trend.empty and p_trend["COLD"].values[0]:
    st.error("Joueur en difficulte (COLD)")
else:
    st.info("Forme neutre")

# --- Chart ---
st.subheader("Points sur les 7 derniers matchs")
st.line_chart(
    p_games.set_index("GAME_DATE")["PTS"]
)

# --- Betting model ---
st.subheader("Analyse du pari (Points)")

line = st.number_input(
    "Ligne bookmaker (PTS)",
    value=float(round(p_avg["PTS_AVG"].values[0], 1))
)

mean = p_avg["PTS_AVG"].values[0]
std = p_games["PTS"].std()
if pd.isna(std):
    std = 5

prob_over = 1 - norm.cdf(line, mean, std)

st.write("Probabilite Over :", round(prob_over * 100, 1), "%")

if prob_over > 0.6:
    st.success("PARI RECOMMANDE : OVER")
elif prob_over < 0.4:
    st.error("PARI RECOMMANDE : UNDER")
else:
    st.warning("PAS DE VALUE CLAIRE")
    
st.subheader("Suivi bankroll et ROI")

bets = pd.read_csv("data/bets_history.csv")

if len(bets) > 0:
    total_stake = bets["STAKE"].sum()
    total_profit = bets["PROFIT"].sum()
    roi = (total_profit / total_stake) * 100 if total_stake > 0 else 0
    winrate = (bets["RESULT"] == "WIN").mean() * 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Paris", len(bets))
    c2.metric("Mise totale", round(total_stake, 2))
    c3.metric("Profit net", round(total_profit, 2))
    c4.metric("ROI %", round(roi, 2))

    bets["BANKROLL"] = bets["PROFIT"].cumsum()
    st.line_chart(bets["BANKROLL"])
else:
    st.info("Aucun pari enregistre pour le moment")

st.subheader("Probabilites autres marches")

market = st.selectbox(
    "Choisir le marche",
    ["PTS", "PRA", "AST", "REB"]
)

line_prop = st.number_input(
    "Ligne bookmaker",
    value=float(
        props[
            (props["PLAYER_NAME"] == player) &
            (props["STAT"] == market)
        ]["MEAN"].values[0]
    )
)

row = props[
    (props["PLAYER_NAME"] == player) &
    (props["STAT"] == market)
].iloc[0]

mean = row["MEAN"]
std = row["STD"]

prob_over = 1 - norm.cdf(line_prop, mean, std)

st.write("Probabilite Over :", round(prob_over * 100, 1), "%")

if prob_over > 0.6:
    st.success("PARI RECOMMANDE : OVER")
elif prob_over < 0.4:
    st.error("PARI RECOMMANDE : UNDER")
else:
    st.warning("PAS DE VALUE CLAIRE")




