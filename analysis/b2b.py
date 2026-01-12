from nba_api.stats.endpoints import leaguegamefinder
from datetime import datetime, timedelta

def is_back_to_back(team_abbr: str) -> bool:
    """
    Retourne True si l'équipe joue un back-to-back
    (a joué la veille)
    team_abbr: ex 'ATL', 'BOS'
    """
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

    finder = leaguegamefinder.LeagueGameFinder(
        team_abbreviation_nullable=team_abbr,
        date_from_nullable=yesterday,
        date_to_nullable=yesterday
    )

    games = finder.get_data_frames()[0]
    return not games.empty
