from nba_api.stats.endpoints import leaguegamefinder
from datetime import datetime, timedelta

def is_back_to_back(team_id):
    yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    finder = leaguegamefinder.LeagueGameFinder(
        team_id_nullable=team_id,
        date_from_nullable=yesterday,
        date_to_nullable=yesterday
    )

    games = finder.get_data_frames()[0]
    return not games.empty