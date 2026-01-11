import pandas as pd
import numpy as np
from scipy.stats import norm

THRESHOLD = 0.57
STAKE = 10

games = pd.read_parquet("data_export/games.parquet")
props = pd.read_parquet("data_export/props.parquet")
defense = pd.read_parquet("data_export/defense.parquet")

games["PRA"] = games["PTS"] + games["REB"] + games["AST"]
defense["COEF_DEF"] = defense["DEF_RATING"] / defense["DEF_RATING"].mean()

results = []

for _, row in props[props["STAT"] == "PRA"].iterrows():
    player = row["PLAYER_NAME"]
    mean = row["MEAN"]
    std = row["STD"] if row["STD"] > 0 else 1

    p_games = games[games["PLAYER_NAME"] == player]
    if p_games.empty:
        continue

    for _, g in p_games.iterrows():
        team = g["MATCHUP"].split(" ")[-1]
        if team not in defense["TEAM"].values:
            continue

        adj_mean = mean * defense[defense["TEAM"] == team]["COEF_DEF"].values[0]
        line = adj_mean + np.random.normal(0, std * 0.5)
        prob = 1 - norm.cdf(line, adj_mean, std)

        if prob < THRESHOLD:
            continue

        win = g["PRA"] > line
        profit = STAKE * 0.9 if win else -STAKE
        results.append(profit)

if not results:
    print("Aucun pari genere")
else:
    print("Paris:", len(results))
    print("Winrate:", round(sum(p > 0 for p in results) / len(results) * 100, 2), "%")
    print("Profit:", round(sum(results), 2))
