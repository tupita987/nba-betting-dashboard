import pandas as pd
from scipy.stats import norm

# PARAMETRES
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
    if stat not in p_games.columns:
        continue

    for _, g in p_games.iterrows():
        line = mean
        prob = 1 - norm.cdf(line, mean, std)

        if prob < THRESHOLD:
            continue

        real = g[stat]
        win = real > line

        profit = STAKE * 0.9 if win else -STAKE

        results.append({
            "PLAYER": player,
            "STAT": stat,
            "WIN": win,
            "PROFIT": profit
        })

df = pd.DataFrame(results)

print("Paris:", len(df))
print("Winrate:", round(df["WIN"].mean() * 100, 2), "%")
print("Profit total:", round(df["PROFIT"].sum(), 2))
