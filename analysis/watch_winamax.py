import pandas as pd
from pathlib import Path
from scipy.stats import norm
from alerts import send_alert
import os

# ================= CONFIG =================
DATA_STATE = Path("data/winamax_state.csv")
DATA_STATE.parent.mkdir(exist_ok=True)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ================= FONCTIONS =================
def apply_context_penalty(prob, home, b2b):
    penalty = 0.0
    if not home:
        penalty += 0.03   # Away
    if b2b:
        penalty += 0.04   # Back-to-back
    return max(prob - penalty, 0)

def kelly_light(prob, odds, bankroll=100):
    edge = prob * (odds - 1) - (1 - prob)
    if edge <= 0:
        return 0
    kelly = edge / (odds - 1)
    return round(bankroll * kelly * 0.25, 2)

# ================= CHARGEMENT DONNÉES =================
games = pd.read_csv("data/players_7_games.csv")
props = pd.read_csv("data/props_model.csv")

if "PRA" not in games.columns:
    games["PRA"] = games["PTS"] + games["REB"] + games["AST"]

# ================= ÉTAT PRÉCÉDENT =================
if DATA_STATE.exists():
    state = pd.read_csv(DATA_STATE)
else:
    state = pd.DataFrame(columns=["PLAYER_NAME", "LINE"])

# ================= SIMULATION WINAMAX =================
# (sera remplacé plus tard par un vrai fetch)
winamax = props.copy()

for _, row in winamax.iterrows():
    player = row["PLAYER_NAME"]
    ligne = row["MEAN"]
    cote = row.get("ODDS", None)

    # Ligne ou cote non publiée
    if cote is None or pd.isna(cote):
        continue

    # Déjà alerté pour cette ligne
    old = state[state["PLAYER_NAME"] == player]
    if not old.empty and old.iloc[0]["LINE"] == ligne:
        continue

    p_games = games[games["PLAYER_NAME"] == player]
    if len(p_games) < 5:
        continue

    # ================= CONTEXTE MATCH =================
    last_game = p_games.sort_values("GAME_DATE").iloc[-1]
    matchup = last_game["MATCHUP"]

    home = "vs" in matchup
    b2b = False  # à brancher plus tard automatiquement

    # ================= PRA MODÈLE =================
    pra = p_games.sort_values("GAME_DATE").tail(7)["PRA"].mean()
    std = p_games["PRA"].std()
    if pd.isna(std) or std < 1:
        std = 5

    prob_raw = 1 - norm.cdf(ligne, pra, std)
    prob = apply_context_penalty(prob_raw, home, b2b)

    proba_cote = 1 / cote

    # ================= DÉCISION =================
    if prob >= 0.62 and prob > proba_cote + 0.05:
        mise = kelly_light(prob, cote, bankroll=100)

        send_alert(
            BOT_TOKEN,
            CHAT_ID,
            player=player,
            matchup=matchup,
            home=home,
            b2b=b2b,
            model_line=round(pra, 1),
            book_line=ligne,
            odds=cote,
            prob=prob
        )

    # ================= MÉMORISATION =================
    state = pd.concat([
        state,
        pd.DataFrame([{
            "PLAYER_NAME": player,
            "LINE": ligne
        }])
    ])

state.to_csv(DATA_STATE, index=False)
