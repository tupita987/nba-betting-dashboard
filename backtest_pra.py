import pandas as pd
import numpy as np
from scipy.stats import norm

# ==============================
# PARAMÈTRES (à tester)
# ==============================
PROB_MIN = 0.57
VALUE_MIN = 0.12
P90_MARGIN = 8

ODDS = 1.90          # cote moyenne
STAKE = 1.0          # mise fixe par pari

# ==============================
# LOAD DATA
# ==============================
games = pd.read_parquet("data_export/games.parquet")
props = pd.read_parquet("data_export/props.parquet")

games["PRA"] = games["PTS"] + games["REB"] + games["AST"]

# ==============================
# BACKTEST
# ==============================
results = []

for _, row in props.iterrows():

    if row.get("STAT") != "PRA":
        continue

    player = row["PLAYER_NAME"]
    mean = row["MEAN"]
    std = row["STD"] if row["STD"] > 0 else 1
    line = mean

    p_games = games[games["PLAYER_NAME"] == player]
    if len(p_games) < 10:
        continue

    p90 = p_games["PRA"].quantile(0.9)
    prob_over = 1 - norm.cdf(line, mean, std)
    value = abs(prob_over - 0.5)

    if not (
        prob_over >= PROB_MIN and
        value >= VALUE_MIN and
        p90 <= line + P90_MARGIN
    ):
        continue

    # --- Résultat réel (dernier match connu) ---
    actual = p_games.sort_values("GAME_DATE").iloc[-1]["PRA"]
    win = actual > line

    profit = STAKE * (ODDS - 1) if win else -STAKE

    results.append({
        "PLAYER": player,
        "LINE": round(line, 1),
        "ACTUAL": actual,
        "WIN": win,
        "PROFIT": profit
    })

# ==============================
# ANALYSE
# ==============================
df = pd.DataFrame(results)

if df.empty:
    print("Aucun pari détecté avec ces paramètres.")
    exit()

print("Nombre de paris :", len(df))
print("Winrate :", round(df["WIN"].mean() * 100, 2), "%")
print("Profit total :", round(df["PROFIT"].sum(), 2))
print("ROI :", round(df["PROFIT"].sum() / (len(df) * STAKE) * 100, 2), "%")

# ==============================
# DRAWNDOWN
# ==============================
df["BANKROLL"] = df["PROFIT"].cumsum()
drawdown = df["BANKROLL"] - df["BANKROLL"].cummax()
print("Drawdown max :", round(drawdown.min(), 2))
