def explain(decision, prob, value, p90, line):
    reasons = []

    if prob < 0.58:
        reasons.append("Probabilité trop faible")
    if value < 0.12:
        reasons.append("Pas assez de value")
    if p90 > line + 6:
        reasons.append("Distribution trop large")

    if decision != "NO BET":
        return "Critères validés"

    return " | ".join(reasons)
