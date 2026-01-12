import itertools

def build_best_combo(over_df):
    """
    Retourne le MEILLEUR combiné intelligent (max 2 legs)
    """
    best = None
    best_score = 0

    players = over_df.to_dict("records")

    for combo in itertools.combinations(players, 2):
        matchups = {p["MATCHUP"] for p in combo}
        if len(matchups) < 2:
            continue

        prob = combo[0]["PROB"] * combo[1]["PROB"]
        odds = combo[0]["ODDS"] * combo[1]["ODDS"]

        score = prob * odds  # critère EV simple

        if score > best_score:
            best_score = score
            best = {
                "players": [combo[0]["PLAYER_NAME"], combo[1]["PLAYER_NAME"]],
                "prob": prob,
                "odds": round(odds, 2)
            }

    return best
