from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
import pandas as pd
import time

def load_players_games(season="2023-24", n_games=7, max_players=30):
    all_players = players.get_active_players()[:max_players]
    rows = []

    for p in all_players:
        try:
            df = playergamelog.PlayerGameLog(
                player_id=p["id"],
                season=season
            ).get_data_frames()[0].head(n_games)

            if df.empty:
                continue

            df["PLAYER_NAME"] = p["full_name"]
            rows.append(df)

            time.sleep(0.4)  # IMPORTANT for cloud
        except Exception as e:
            continue

    if len(rows) == 0:
        return pd.DataFrame()

    return pd.concat(rows, ignore_index=True)
