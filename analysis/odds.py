import requests
import pandas as pd

BASE = "https://api.the-odds-api.com/v4"

def fetch_winamax_pra(api_key: str) -> pd.DataFrame:
    """
    Récupère les PRA joueurs NBA depuis Winamax (The Odds API).
    Retourne un DataFrame VIDE si non dispo (SAFE).
    """
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
                for o in market.get("outcomes", []):
                    name = o.get("name")
                    price = o.get("price")

                    if not name or price is None:
                        continue

                    # Exemple attendu : "Jalen Johnson Over 31.5"
                    if " Over " not in name:
                        continue

                    try:
                        player, line = name.split(" Over ")
                        line = float(line)
                    except Exception:
                        continue

                    rows.append({
                        "PLAYER_NAME": player.strip(),
                        "LINE": line,
                        "ODDS": float(price)
                    })

    return pd.DataFrame(rows)
