import pandas as pd
from pathlib import Path
from scipy.stats import norm
from alerts import send_alert
import os
from datetime import timedelta

# ================= CONFIG =================
DATA_STATE = Path("data/winamax_state.csv")
DATA_STATE.parent.mkdir(exist_ok=True)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

BANKROLL = 100
MAX_COMBO_LEGS = 2

# ================= FONCTIONS =================
def apply_context_penalty(prob, home, b2b):
    penalty = 0.0
    if not home:
        penalty += 0.03
    if b2b:
        penalty += 0.04
    return max(prob - penalty, 0)

def kelly_light(prob, odds, bankroll):
    edge = prob * (odds - 1) - (1 - prob)
    if edge <= 0:
        return 0.0
    kelly = edge / (odds - 1)
    return round(bankroll * kelly * 0.25, 2)

def is_b2b(player_games):
    if len(player_games) < 2:
        return False
    last_two = player_games.sort_values("GAME_DATE").tail(2)
    d1 = pd.to_datetime(last_two.iloc[0]["GAME_DATE"])
    d2 = pd.to_datetime(last_two.iloc[1]["GAME_DATE"])
    return (d2 - d1).days == 1

# ================= CHARGEMENT DONNÉES =================
games = pd.read_csv("data/players_7_games.csv")
props = pd.read_csv("data/props_model.csv")

if "PRA" not in games.columns:
    games["PRA"] = games["PTS"] + games["REB"] + games["AST"]

if DATA_STATE.exists():
    state = pd.read_csv(DATA_STATE)
else:
    state = pd.DataFrame(columns=["PLAYER_NAME", "LINE"])

winamax = props.copy()
signals = []

# ================= ANALYSE =================
for _, row in winamax.iterrows():
    player = row["PLAYER_NAME"]
    ligne = row["MEAN"]
    cote = row.get("ODDS", None)

    if cote is None or pd.isna(cote):
        continue

    old = state[state["PLAYER_NAME"] == player]
    if not old.empty and old.iloc[0]["LINE"] == ligne:
        continue

    p_games = games[games["PLAYER_NAME"] == player]
    if len(p_games) < 5:
        continue

    last_game = p_games.sort_values("GAME_DATE").iloc[-1]
    matchup = last_game["MATCHUP"]

    home = "vs" in matchup
    b2b = is_b2b(p_games)

    pra = p_games.sort_values("GAME_DATE").tail(7)["PRA"].mean()
    std = p_games["PRA"].std() or 5

    prob_raw = 1 - norm.cdf(ligne, pra, std)
    prob = apply_context_penalty(prob_raw, home, b2b)

    proba_cote = 1 / cote
    stake = kelly_light(prob, cote, BANKROLL)

    if stake > 0 and prob >= 0.62 and prob > proba_cote + 0.05:
        signals.append({
            "player": player,
            "matchup": matchup,
            "home": home,
            "b2b": b2b,
            "pra": round(pra, 1),
            "ligne": ligne,
            "cote": cote,
            "prob": prob,
            "stake": stake
        })

    state = pd.concat([
        state,
        pd.DataFrame([{"PLAYER_NAME": player, "LINE": ligne}])
    ])

state.to_csv(DATA_STATE, index=False)

# ================= COMBINÉ INTELLIGENT =================
signals = sorted(signals, key=lambda x: x["prob"], reverse=True)

if len(signals) >= 2:
    combo = signals[:MAX_COMBO_LEGS]
    combo_prob = 1
    combo_odds = 1

    for s in combo:
        combo_prob *= s["prob"]
        combo_odds *= s["cote"]

    combo_stake = kelly_light(combo_prob, combo_odds, BANKROLL)

    if combo_stake >= 1:
        send_alert(
            BOT_TOKEN,
            CHAT_ID,
            player=" + ".join([s["player"] for s in combo]),
            matchup=" | ".join([s["matchup"] for s in combo]),
            home=True,
            b2b=False,
            model_line="-",
            book_line="-",
            odds=round(combo_odds, 2),
            prob=combo_prob,
            stake=combo_stake,
            combo=True
        )
