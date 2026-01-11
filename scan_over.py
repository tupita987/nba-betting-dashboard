import os
import pandas as pd
import requests
from scipy.stats import norm

print("=== PRA SCAN START ===")

# ==================================================
# TELEGRAM (via secrets GitHub)
# ==================================================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError("Secrets Telegram manquants")

def send_alert(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    r = requests.post(url, data=payload, timeout=10)
    print("Telegram:", r.status_code)

# ==================================================
# LOAD DATA
# ==================================================
games = pd.read_parquet("data_export/games.parquet")
props = pd.read_parquet("data_export/props.parquet")

print("Data loaded")
print("Games rows:", len(games))
print("Props rows:", len(props))

# ==================================================
# PREP
# ==================================================
games["PRA"] = games["PTS"] + games["REB"] + games["AST"]

# ==================================================
# SCAN PRA OVER
# ==================================================
alerts_sent = 0

for _, row in props.iterrows():

    if row.get("STAT") != "PRA":
        continue

    player = row["PLAYER_NAME"]
    mean = row["MEAN"]
    std = row["STD"] if row["STD"] > 0 else 1
    line = mean  # ligne théorique (props.parquet)

    p_games = games[games["PLAYER_NAME"] == player]
    if len(p_games) < 5:
        continue

    p90 = p_games["PRA"].quantile(0.9)
    prob_over = 1 - norm.cdf(line, mean, std)
    value = abs(prob_over - 0.5)

    if prob_over >= 0.57 and value >= 0.12 and p90 <= line + 8:

        message = (
            "🔥 OVER PRA AUTO\n\n"
            f"👤 {player}\n"
            f"📏 Ligne : {round(line,1)}\n"
            f"📈 Proba : {round(prob_over*100,1)} %\n"
            f"📊 P90 : {round(p90,1)}"
        )

        send_alert(message)
        alerts_sent += 1

print("Scan terminé. Alertes envoyées:", alerts_sent)
print("=== PRA SCAN END ===")
