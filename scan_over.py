import os
import pandas as pd
import requests
from scipy.stats import norm
from datetime import datetime

# ==============================
# CONFIG
# ==============================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError("Secrets Telegram manquants")

LOG_FILE = "alerts_log.csv"
TODAY = datetime.utcnow().strftime("%Y-%m-%d")

# ==============================
# TELEGRAM
# ==============================
def send_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload, timeout=10)

# ==============================
# LOAD DATA
# ==============================
games = pd.read_parquet("data_export/games.parquet")
props = pd.read_parquet("data_export/props.parquet")

games["PRA"] = games["PTS"] + games["REB"] + games["AST"]

# ==============================
# LOAD / INIT LOG
# ==============================
if os.path.exists(LOG_FILE):
    log = pd.read_csv(LOG_FILE)
else:
    log = pd.DataFrame(columns=["date", "player", "line", "prob"])

alerts_today = []

# ==============================
# SCAN PRA
# ==============================
for _, row in props.iterrows():

    if row.get("STAT") != "PRA":
        continue

    player = row["PLAYER_NAME"]
    mean = row["MEAN"]
    std = row["STD"] if row["STD"] > 0 else 1
    line = mean

    # --- anti-spam journalier ---
    already_sent = log[
        (log["date"] == TODAY) &
        (log["player"] == player)
    ]

    if not already_sent.empty:
        continue

    p_games = games[games["PLAYER_NAME"] == player]
    if len(p_games) < 5:
        continue

    p90 = p_games["PRA"].quantile(0.9)
    prob_over = 1 - norm.cdf(line, mean, std)
    value = abs(prob_over - 0.5)

    if prob_over >= 0.57 and value >= 0.12 and p90 <= line + 8:

        msg = (
            f"🔥 OVER PRA\n\n"
            f"👤 {player}\n"
            f"📏 Ligne : {round(line,1)}\n"
            f"📈 Proba : {round(prob_over*100,1)} %\n"
            f"📊 P90 : {round(p90,1)}"
        )

        send_alert(msg)

        log.loc[len(log)] = [TODAY, player, line, round(prob_over, 3)]
        alerts_today.append(player)

# ==============================
# SAVE LOG
# ==============================
log.to_csv(LOG_FILE, index=False)

# ==============================
# DAILY SUMMARY (1x / jour)
# ==============================
if datetime.utcnow().hour == 23:
    if alerts_today:
        summary = "📊 RÉSUMÉ DU JOUR\n\n" + "\n".join(
            f"• {p}" for p in alerts_today
        )
    else:
        summary = "📊 RÉSUMÉ DU JOUR\n\nAucun pari value détecté aujourd’hui."

    send_alert(summary)
