from nba_api.stats.endpoints import leaguedashteamstats
import pandas as pd

print("loading team defensive stats")

team_stats = leaguedashteamstats.LeagueDashTeamStats(
    measure_type_detailed_defense="Defense",
    per_mode_detailed="PerGame",
    season="2023-24"
)

df = team_stats.get_data_frames()[0]

print("columns:", list(df.columns))

# Select stable defensive indicators
df_def = df[[
    "TEAM_NAME",
    "GP",
    "DEF_RATING",
    "STL",
    "BLK",
    "OPP_PTS_PAINT",
    "OPP_PTS_FB",
    "OPP_PTS_2ND_CHANCE"
]].copy()

# Rename columns
df_def.columns = [
    "TEAM",
    "GAMES",
    "DEF_RATING",
    "STEALS",
    "BLOCKS",
    "PTS_IN_PAINT_ALLOWED",
    "FASTBREAK_PTS_ALLOWED",
    "SECOND_CHANCE_PTS_ALLOWED"
]

# Rankings (lower DEF_RATING = better defense)
df_def["DEF_RANK"] = df_def["DEF_RATING"].rank()

# Global defensive score (lower = tougher defense)
df_def["DEF_SCORE"] = (
    df_def["DEF_RANK"] +
    df_def["PTS_IN_PAINT_ALLOWED"].rank() +
    df_def["FASTBREAK_PTS_ALLOWED"].rank() +
    df_def["SECOND_CHANCE_PTS_ALLOWED"].rank()
)

# Defensive label
q1 = df_def["DEF_SCORE"].quantile(0.33)
q2 = df_def["DEF_SCORE"].quantile(0.66)

def label_defense(score):
    if score <= q1:
        return "STRONG_DEF"
    elif score >= q2:
        return "WEAK_DEF"
    else:
        return "AVERAGE_DEF"

df_def["DEF_LABEL"] = df_def["DEF_SCORE"].apply(label_defense)

df_def.to_csv("data\\team_defense.csv", index=False)

print("team_defense.csv created")
