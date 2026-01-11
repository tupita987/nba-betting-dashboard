import pandas as pd
from scipy.stats import norm

print("building props model")

games = pd.read_csv("data\\players_7_games.csv")

# Create PRA
games["PRA"] = games["PTS"] + games["REB"] + games["AST"]

stats = ["PTS", "REB", "AST", "PRA"]

rows = []

for player in games["PLAYER_NAME"].unique():
    p_df = games[games["PLAYER_NAME"] == player]

    if len(p_df) < 5:
        continue

    for stat in stats:
        mean = p_df[stat].mean()
        std = p_df[stat].std()

        if pd.isna(std) or std == 0:
            std = 1.0

        rows.append({
            "PLAYER_NAME": player,
            "STAT": stat,
            "MEAN": mean,
            "STD": std
        })

model_df = pd.DataFrame(rows)
model_df.to_csv("data\\props_model.csv", index=False)

print("props_model.csv created")
