from nba_api.stats.endpoints import scoreboardv2
from datetime import datetime

def get_today_games():
    today = datetime.today().strftime("%Y-%m-%d")
    board = scoreboardv2.ScoreboardV2(game_date=today)
    df = board.get_data_frames()[0]

    data = {}

    # HOME TEAM
    if "HOME_TEAM_NAME" in df.columns:
        data["HOME_TEAM_NAME"] = df["HOME_TEAM_NAME"]
    elif "HOME_TEAM_ABBREVIATION" in df.columns:
        data["HOME_TEAM_NAME"] = df["HOME_TEAM_ABBREVIATION"]

    # VISITOR TEAM
    if "VISITOR_TEAM_NAME" in df.columns:
        data["VISITOR_TEAM_NAME"] = df["VISITOR_TEAM_NAME"]
    elif "VISITOR_TEAM_ABBREVIATION" in df.columns:
        data["VISITOR_TEAM_NAME"] = df["VISITOR_TEAM_ABBREVIATION"]

    return data