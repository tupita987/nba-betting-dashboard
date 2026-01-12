from nba_api.stats.endpoints import leaguegamefinder
from datetime import datetime, timedelta

def is_back_to_back(team_abbr: str) -> bool:
    """
    Détection B2B sécurisée.
    Si l'API NBA échoue → retourne False (safe).
    """
    try:
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")

        finder = leaguegamefinder.LeagueGameFinder(
            team_abbreviation_nullable=team_abbr,
            date_from_nullable=yesterday,
            date_to_nullable=yesterday,
            timeout=10
        )

        games = finder.get_data_frames()[0]
        return not games.empty

    except Exception:
        # API down / lente / bloquée → SAFE FALLBACK
        return False
