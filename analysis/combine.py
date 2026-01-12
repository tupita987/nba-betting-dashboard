import itertools

def build_smart_combos(over_df, max_legs=2):
    """
    Construit des combinés intelligents à partir des OVER A
    - max 2 joueurs
    - joueurs de matchs différents
    """
    combos = []

    players = over_df.to_dict("records")

    for combo in itertools.combinations(players, max_legs):
        matchups = {p["MATCHUP"] for p in combo}
        if len(matchups) < len(combo):
            continue  # même match → rejet

        prob_combo = 1
        odds_combo = 1
        names = []

        for p in combo:
            prob_combo *= p["PROB"]
            odds_combo *= p["ODDS"]
            names.append(p["PLAYER_NAME"])

        combos.append({
            "JOUEURS": " + ".join(names),
            "PROB_COMBO": round(prob_combo, 3),
            "ODDS_COMBO": round(odds_combo, 2),
            "LEGS": len(combo)
        })

    return combos
