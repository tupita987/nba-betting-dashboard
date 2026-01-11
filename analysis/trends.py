print("trends.py started")

import pandas as pd

df = pd.read_csv("data\\players_7_games.csv")

print("rows loaded:", len(df))

trends = []

for player in df["PLAYER_NAME"].unique():
    p_df = df[df["PLAYER_NAME"] == player].sort_values("GAME_DATE")

    if len(p_df) < 5:
        continue

    pts_trend = p_df["PTS"].diff().mean()

    trends.append({
        "PLAYER_NAME": player,
        "PTS_TREND": pts_trend,
        "HOT": pts_trend > 1.5,
        "COLD": pts_trend < -1.5
    })

trend_df = pd.DataFrame(trends)
trend_df.to_csv("data\\player_trends.csv", index=False)

print("trends finished")
