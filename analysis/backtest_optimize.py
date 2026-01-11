import pandas as pd
import numpy as np
from scipy.stats import norm

games = pd.read_parquet("data_export/games.parquet")
props = pd.read_parquet("data_export/props.parquet")

games["PRA"] = games["PTS"] + games["REB"] + games["AST"]

STAKE = 10
thresholds = np.arange(0.55, 0.71, 0.01)

rows = []

for threshold in thresholds:
    results = []

    for _, row in props[props["STAT"] == "PRA"].iterrows():
        mean = row["MEAN"]
        std = row["STD"] if row["STD"] > 0 else 1
        player = row["PLAYER_NAME"]

        p_games = games[games["PLAYER_NAME"] == player]
        if p_games.empty:
            continue

        for _, g in p_games.iterrows():
            line = mean + np.random.normal(0, std * 0.5)
            prob = 1 - norm.cdf(line, mean, std)

            if prob < threshold:
                continue

            win = g["PRA"] > line
            profit = STAKE * 0.9 if win else -STAKE
            results.append(profit)

    if results:
        rows.append({
            "THRESHOLD": round(threshold, 2),
            "BETS": len(results),
            "WINRATE": round(sum(p > 0 for p in results) / len(results) * 100, 2),
            "PROFIT": round(sum(results), 2)
        })

df = pd.DataFrame(rows).sort_values("PROFIT", ascending=False)
print(df.head(10))
