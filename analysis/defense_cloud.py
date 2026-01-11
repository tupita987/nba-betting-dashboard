from nba_api.stats.endpoints import leaguedashteamstats
import pandas as pd

def load_team_defense(season="2023-24"):
    df = leaguedashteamstats.LeagueDashTeamStats(
        measure_type_detailed_defense="Defense",
        per_mode_detailed="PerGame",
        season=season
    ).get_data_frames()[0]

    df = df[[
        "TEAM_NAME",
        "DEF_RATING",
        "STL",
        "BLK",
        "OPP_PTS_PAINT",
        "OPP_PTS_FB",
        "OPP_PTS_2ND_CHANCE"
    ]]

    df.columns = [
        "TEAM",
        "DEF_RATING",
        "STEALS",
        "BLOCKS",
        "PTS_PAINT_ALLOWED",
        "FASTBREAK_ALLOWED",
        "SECOND_CHANCE_ALLOWED"
    ]

    return df
