import pandas as pd
import numpy as np

games = pd.read_csv("data\\players_7_games.csv")
agg = pd.read_csv("data\\players_aggregated.csv")
trends = pd.read_csv("data\\player_trends.csv")

# Home / Away
games["HOME"] = games["MATCHUP"].str.contains("vs").astype(int)

# Back to back
games["GAME_DATE"] = pd.to_datetime(games["GAME_DATE"])
games = games.sort_values(["PLAYER_NAME", "GAME_DATE"])
games["B2B"] = games.groupby("PLAYER_NAME")["GAME_DATE"].diff().dt.days.eq(1).astype(int)

# Merge averages
df = games.merge(agg, on="PLAYER_NAME", how="left")
df = df.merge(trends, on="PLAYER_NAME", how="left")

df.to_csv("data\\features_full.csv", index=False)

print("features created")
