from nba_api.stats.endpoints import scoreboardv2
from datetime import datetime

def get_today_games():
    today = datetime.today().strftime("%Y-%m-%d")
    board = scoreboardv2.ScoreboardV2(game_date=today)
    df = board.get_data_frames()[0]

    # Colonnes possibles selon l'API
    possible_cols = {
        "HOME_TEAM_NAME": ["HOME_TEAM_NAME", "HOME_TEAM_ABBREVIATION"],
        "VISITOR_TEAM_NAME": ["VISITOR_TEAM_NAME", "VISITOR_TEAM_ABBREVIATION"],
        "HOME_TEAM_ID": ["HOME_TEAM_ID"],
        "VISITOR_TEAM_ID": ["VISITOR_TEAM_ID"],
    }

    data = {}

    for key, variants in possible_cols.items():
        for col in variants:
            if col in df.columns:
                data[key] = df[col]
                break

    return data