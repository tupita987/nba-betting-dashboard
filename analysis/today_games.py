from nba_api.stats.endpoints import scoreboardv2
import pandas as pd

print("loading scoreboard")

board = scoreboardv2.ScoreboardV2()
dfs = board.get_data_frames()

print("number of tables:", len(dfs))

games = dfs[0]

print("columns found:")
print(list(games.columns))

# Keep only columns that exist
cols = []
for c in [
    "GAME_ID",
    "GAME_DATE_EST",
    "HOME_TEAM_NAME",
    "VISITOR_TEAM_NAME"
]:
    if c in games.columns:
        cols.append(c)

games = games[cols]

print("final columns:", list(games.columns))
print("number of games:", len(games))

games.to_csv("data\\today_games.csv", index=False)

print("today_games.csv created")
