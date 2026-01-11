import pandas as pd
import numpy as np
from scipy.stats import norm

THRESHOLD = 0.60
STAKE = 10

games = pd.read_parquet("data_export/games.parquet")
props = pd.read_parquet("data_export/props.parquet")

games["PRA"] = games["PTS"] + games["REB"] + games["AST"]

results = []

for _, row in props.iterrows():
    player = row["PLAYER_NAME"]
    stat = row["STAT"]
    mean = row["MEAN"]
    std = row["STD"] if row["STD"] > 0 else 1

    p_games = games[games["PLAYER_NAME"] == player]
    if stat not in p_games.columns or p_games.empty:
        continue

    for _, g in p_games.iterrows():

        # Simulated bookmaker line (mean +- noise)
        line = mean + np.random.normal(0, std * 0.5)

        prob = 1 - norm.cdf(line, mean, std)

        if prob < THRESHOLD:
            continue

        real = g[stat]
        win = real > line

        profit = STAKE * 0.9 if win else -STAKE

        results.append({
            "PLAYER": player,
            "STAT": stat,
            "LINE": round(line, 2),
            "REAL": real,
            "WIN": win,
            "PROFIT": profit
        })

# ===== RESULTATS =====
df = pd.DataFrame(results)

if df.empty:
    print("Aucun pari genere avec ce seuil.")
    print("Essaye de baisser THRESHOLD (ex: 0.55).")
else:
    print("Nombre de paris:", len(df))
    print("Winrate:", round(df["WIN"].mean() * 100, 2), "%")
    print("Profit total:", round(df["PROFIT"].sum(), 2))
