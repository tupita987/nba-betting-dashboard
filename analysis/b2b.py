from datetime import datetime, timedelta
from nba_api.stats.endpoints import leaguegamefinder

def is_back_to_back(team_abbr: str) -> bool:
    try:
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        finder = leaguegamefinder.LeagueGameFinder(
            team_abbreviation_nullable=team_abbr,
            date_from_nullable=yesterday,
            date_to_nullable=yesterday,
            timeout=8
        )
        return not finder.get_data_frames()[0].empty
    except Exception:
        return False
