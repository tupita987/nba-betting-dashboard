import pandas as pd
import numpy as np
from scipy.stats import norm

df = pd.read_csv("data\\features_full.csv")

def over_probability(avg, std, line):
    return 1 - norm.cdf(line, avg, std)

player_std = df.groupby("PLAYER_NAME")["PTS"].std().reset_index()
player_std.columns = ["PLAYER_NAME", "PTS_STD"]

df = df.merge(player_std, on="PLAYER_NAME")

df["PTS_STD"] = df["PTS_STD"].fillna(5)

df.to_csv("data\\model_ready.csv", index=False)

print("model data ready")
