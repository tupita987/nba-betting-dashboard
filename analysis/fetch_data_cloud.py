from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
import pandas as pd
import time

def load_players_games(season="2023-24", n_games=7):
    all_players = players.get_active_players()
    rows = []

    for p in all_players:
        try:
            df = playergamelog.PlayerGameLog(
                player_id=p["id"],
                season=season
            ).get_data_frames()[0].head(n_games)

            df["PLAYER_NAME"] = p["full_name"]
            rows.append(df)
            time.sleep(0.3)
        except:
            continue

    return pd.concat(rows, ignore_index=True)
