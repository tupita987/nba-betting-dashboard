# analysis/odds.py
import requests
import pandas as pd
import time
from typing import Optional

BASE = "https://api.the-odds-api.com/v4"

def _safe_get(url, params, timeout=10):
    try:
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None

def fetch_winamax_player_props(api_key: str, sport: str = "basketball_nba", region: str = "eu", market: str = "player_props", bookmaker_key: str = "winamax_fr"):
    """
    Récupère (si disponibles) les player props de Winamax pour le sport donné.
    Retour: DataFrame columns = [player, stat, line, price, bookmaker, event_id, start_time]
    NOTE: la structure exacte dépend de l'API fournisseur. Cette fonction est robuste:
    - elle récupère d'abord la liste d'événements pour le sport,
    - puis pour chaque event tente de récupérer les marchés /player props/ pour winamax_fr.
    """
    results = []

    # 1) récupérer événements pour le sport (v4 endpoint)
    events_url = f"{BASE}/sports/{sport}/odds"
    params = {
        "apiKey": api_key,
        "regions": region,
        "markets": "totals,player_props,alternatives",  # tenter plusieurs keys
        "oddsFormat": "decimal",
        "bookmakers": bookmaker_key
    }
    events = _safe_get(events_url, params)
    if not events:
        # fallback: récupérer événements sans bookmakers (ensuite interroger event par event)
        params2 = {"apiKey": api_key, "regions": region, "oddsFormat": "decimal"}
        events = _safe_get(f"{BASE}/sports/{sport}/odds", params2) or []

    # 2) pour chaque event, tenter d'obtenir la section 'player props' spécifiquement
    for ev in events:
        event_id = ev.get("id") or ev.get("event_id") or ev.get("event_key") or ev.get("key")
        start_time = ev.get("commence_time") or ev.get("start_time")
        # Try event-level endpoint
        if event_id:
            url_event = f"{BASE}/events/{event_id}/odds"
            params_ev = {"apiKey": api_key, "bookmakers": bookmaker_key, "oddsFormat": "decimal"}
            ev_data = _safe_get(url_event, params_ev)
            if not ev_data:
                # sometimes the API returns nested 'bookmakers' in events list; try to parse ev directly
                ev_data = ev

            # Parse bookmaker offers inside ev_data
            bookmakers = []
            if isinstance(ev_data, dict):
                bookmakers = ev_data.get("bookmakers") or ev_data.get("sites") or []
            elif isinstance(ev_data, list):
                # if the event returned as list, pick first
                first = ev_data[0] if ev_data else {}
                bookmakers = first.get("bookmakers") or first.get("sites") or []
            else:
                bookmakers = []

            for bk in bookmakers:
                key = bk.get("key") or bk.get("bookmaker_key") or bk.get("title") or bk.get("name")
                if key and bookmaker_key in str(key).lower():
                    markets = bk.get("markets") or bk.get("markets_list") or bk.get("odds") or []
                    # markets varies by API; try to parse any player prop-like markets
                    for m in markets:
                        m_key = m.get("key") or m.get("market_key") or m.get("market")
                        outcomes = m.get("outcomes") or m.get("selections") or m.get("lines") or []
                        # Try to find player prop lines, e.g. outcomes with name containing '+' or 'PTS' or 'PRA'
                        for o in outcomes:
                            name = o.get("name") or o.get("participant") or o.get("label")
                            price = o.get("price") or o.get("odds") or o.get("price_decimal")
                            # Infer stat and line from name when possible
                            # Example name formats: "Player Name - Over 18.5", "Player Name O18.5", "Player Name P+R+A O18.5"
                            if not name:
                                continue
                            # Heuristics to parse player and line
                            # Try "Player Name O18.5" or "Player Name - Over 18.5"
                            import re
                            # capture line like 18.5 or 18
                            m_line = re.search(r'([OU]ver|O|U|Over|Under)?\s*([0-9]{1,2}(?:[.,][05])?)', name, flags=re.IGNORECASE)
                            # try to capture player name before dash
                            parts = re.split(r'\s-\s|\s@\s|\svs\s', name, flags=re.IGNORECASE)
                            player_name = parts[0].strip()
                            line_value = None
                            if m_line:
                                try:
                                    line_value = float(m_line.group(2).replace(',', '.'))
                                except:
                                    line_value = None
                            # Only collect when price exists
                            if price is None:
                                continue
                            results.append({
                                "player": player_name,
                                "stat": "PRA",
                                "line": line_value,
                                "price": float(price) if isinstance(price, (int,float,str)) and str(price).replace('.','',1).replace(',','',1).lstrip('-').isdigit() else None,
                                "bookmaker": key,
                                "event_id": event_id,
                                "start_time": start_time
                            })
            # rate limit safety
            time.sleep(0.3)

    if not results:
        # last-resort: attempt to parse top-level events object for bookmakers entries
        for ev in events:
            bklist = ev.get("bookmakers") or ev.get("sites") or []
            for bk in bklist:
                key = bk.get("key") or bk.get("title") or bk.get("name")
                if key and bookmaker_key in str(key).lower():
                    markets = bk.get("markets") or bk.get("odds") or []
                    for m in markets:
                        outcomes = m.get("outcomes") or []
                        for o in outcomes:
                            name = o.get("name") or o.get("participant") or o.get("label")
                            price = o.get("price")
                            if not name or price is None:
                                continue
                            # best-effort parse
                            import re
                            parts = re.split(r'\s-\s|\s@\s|\svs\s', name, flags=re.IGNORECASE)
                            player_name = parts[0].strip()
                            m_line = re.search(r'([0-9]{1,2}(?:[.,][05])?)', name)
                            line_value = float(m_line.group(1).replace(',', '.')) if m_line else None
                            results.append({
                                "player": player_name,
                                "stat": "PRA",
                                "line": line_value,
                                "price": float(price) if isinstance(price, (int,float)) else None,
                                "bookmaker": key,
                                "event_id": ev.get("id") or ev.get("event_id"),
                                "start_time": ev.get("commence_time")
                            })

    df = pd.DataFrame(results)
    # normalize player names (strip)
    if not df.empty:
        df["player"] = df["player"].str.replace(r'\s+', ' ', regex=True).str.strip()
    return df
