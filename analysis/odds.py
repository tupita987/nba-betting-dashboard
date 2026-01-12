import requests
import pandas as pd

BASE = "https://api.the-odds-api.com/v4"

def fetch_winamax_pra(api_key: str):
    url = f"{BASE}/sports/basketball_nba/odds"
    params = {
        "apiKey": api_key,
        "regions": "eu",
        "markets": "player_props",
        "bookmakers": "winamax_fr",
        "oddsFormat": "decimal"
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return pd.DataFrame()

    rows = []
    for ev in data:
        for bk in ev.get("bookmakers", []):
            if "winamax" not in bk.get("key", ""):
                continue
            for market in bk.get("markets", []):
                if "player" not in market.get("key", ""):
                    continue
                for o in market.get("outcomes", []):
                    name = o.get("name", "")
                    price = o.get("price")
                    if price is None:
                        continue

                    if " Over " not in name:
                        continue

                    player, line = name.split(" Over ")
                    try:
                        line = float(line)
                    except:
                        continue

                    rows.append({
                        "PLAYER_NAME": player.strip(),
                        "STAT": "PRA",
                        "LINE": line,
                        "ODDS": price,
                        "BOOKMAKER": "Winamax"
                    })

    return pd.DataFrame(rows)
