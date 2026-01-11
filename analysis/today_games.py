from nba_api.stats.endpoints import scoreboardv2
from datetime import datetime

def get_today_games():
    today = datetime.today().strftime("%Y-%m-%d")
    board = scoreboardv2.ScoreboardV2(game_date=today)
    df = board.get_data_frames()[0]

    return df[[
        "HOME_TEAM_ID",
        "HOME_TEAM_NAME",
        "VISITOR_TEAM_ID",
        "VISITOR_TEAM_NAME"
    ]]