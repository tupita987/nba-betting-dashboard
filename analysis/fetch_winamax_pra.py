import requests
import pandas as pd
from pathlib import Path
import time

OUT = Path("data/winamax_pra.csv")
OUT.parent.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Referer": "https://www.winamax.fr/"
}

# Endpoint public (utilisé par le site – peut évoluer)
URL = "https://www.winamax.fr/paris-sportifs/sports/2/7/153"

def fetch():
    r = requests.get(URL, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()

def extract_pra(data):
    rows = []
    # Parcours large et sécurisé
    for ev in data.get("matches", []):
        markets = ev.get("markets", [])
        for m in markets:
            name = (m.get("name") or "").lower()
            if "points + rebonds + passes" in name or "pra" in name:
                for o in m.get("selections", []):
                    player = o.get("competitor", "")
                    line = o.get("handicap")
                    odds = o.get("odds")
                    if player and line and odds:
                        rows.append({
                            "PLAYER_NAME": player.strip(),
                            "LINE": float(line),
                            "ODDS": float(odds)
                        })
    return pd.DataFrame(rows).drop_duplicates()

def main():
    try:
        data = fetch()
        df = extract_pra(data)
        if not df.empty:
            df.to_csv(OUT, index=False)
    except Exception:
        pass

if __name__ == "__main__":
    main()