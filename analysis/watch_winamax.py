import pandas as pd
import requests
from pathlib import Path
from scipy.stats import norm
from alerts import send_alert

DATA_STATE = Path("data/winamax_state.csv")
DATA_STATE.parent.mkdir(exist_ok=True)

# === CONFIG TELEGRAM ===
BOT_TOKEN = "<TON_BOT_TOKEN>"
CHAT_ID = "<TON_CHAT_ID>"

# === CHARGEMENT MODELE ===
games = pd.read_csv("data/players_7_games.csv")
props = pd.read_csv("data/props_model.csv")

if "PRA" not in games.columns:
    games["PRA"] = games["PTS"] + games["REB"] + games["AST"]

# === ÉTAT PRÉCÉDENT ===
if DATA_STATE.exists():
    state = pd.read_csv(DATA_STATE)
else:
    state = pd.DataFrame(columns=["PLAYER_NAME", "LINE"])

# === SIMULATION : lignes Winamax mises à jour ===
# ⚠️ ICI tu remplaceras par ton fetch Winamax réel plus tard
winamax = props.copy()  # provisoire

alerts_sent = []

for _, row in winamax.iterrows():
    player = row["PLAYER_NAME"]
    ligne = row["MEAN"]
    cote = row.get("ODDS", None)

    if cote is None:
        continue

    # Déjà traité ?
    old = state[state["PLAYER_NAME"] == player]
    if not old.empty and old.iloc[0]["LINE"] == ligne:
        continue

    p_games = games[games["PLAYER_NAME"] == player]
    if len(p_games) < 5:
        continue

    pra = p_games.sort_values("GAME_DATE").tail(7)["PRA"].mean()
    std = p_games["PRA"].std() or 5

    prob = 1 - norm.cdf(ligne, pra, std)
    proba_cote = 1 / cote

    if prob >= 0.62 and prob > proba_cote + 0.05:
        send_alert(
            BOT_TOKEN,
            CHAT_ID,
            f"🔥 OVER PRA détecté\n\n"
            f"👤 {player}\n"
            f"📊 Ligne : {ligne}\n"
            f"💰 Cote : {cote}\n"
            f"📈 Proba modèle : {round(prob*100,1)} %"
        )
        alerts_sent.append(player)

    state = pd.concat([state, pd.DataFrame([{
        "PLAYER_NAME": player,
        "LINE": ligne
    }])])

state.to_csv(DATA_STATE, index=False)
