print("props.py started")

import pandas as pd

print("loading csv file")
df = pd.read_csv("data\\players_7_games.csv")

print("number of rows:", len(df))

df["PRA"] = df["PTS"] + df["REB"] + df["AST"]

print("aggregating data")

agg = df.groupby("PLAYER_NAME").agg(
    GP=("PTS", "count"),
    PTS_AVG=("PTS", "mean"),
    REB_AVG=("REB", "mean"),
    AST_AVG=("AST", "mean"),
    PRA_AVG=("PRA", "mean"),
    MIN_AVG=("MIN", "mean"),
    FG_PCT=("FG_PCT", "mean"),
    PLUS_MINUS=("PLUS_MINUS", "mean")
).reset_index()

agg.to_csv("data\\players_aggregated.csv", index=False)

print("aggregation finished")
