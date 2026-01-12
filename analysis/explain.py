def expliquer_decision(decision, prob, pra_modele, ligne):
    raisons = []

    if abs(pra_modele - ligne) < 1:
        raisons.append("PRA modèle trop proche de la ligne")

    if prob < 0.55:
        raisons.append("Probabilité insuffisante")

    if decision == "NO BET":
        return " | ".join(raisons) if raisons else "Aucune value détectée"

    if decision == "OVER":
        return "Avantage statistique clair sur la ligne"

    if decision == "UNDER":
        return "Sous-performance attendue"

    return ""
