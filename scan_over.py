import pandas as pd
import requests
from scipy.stats import norm

# ==============================
# TELEGRAM (variables GitHub)
# ==============================
BOT_TOKEN = "${{ secrets.TELEGRAM_BOT_TOKEN }}"
CHAT_ID = "${{ secrets.TELEGRAM_CHAT_ID }}"

def send_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    requests.post(url, data=payload, timeout=5)

# ==============================
# LOAD DATA
# ==============================
games = pd.read_parquet("data_export/games.parquet")
agg = pd.read_parquet("data_export/agg.parquet")
defense = pd.read_parquet("data_export/defense.parquet")
props = pd.read_parquet("data_export/props.parquet")

games["PRA"] = games["PTS"] + games["REB"] + games["AST"]
defense["COEF_DEF"] = defense["DEF_RATING"] / defense["DEF_RATING"].mean()

# ==============================
# SCAN
# ==============================
for _, row in props[props["STAT"] == "PRA"].iterrows():
    player = row["PLAYER_NAME"]

    p_games = games[games["PLAYER_NAME"] == player]
    if len(p_games) < 5:
        continue

    p90 = p_games["PRA"].quantile(0.9)
    mean = row["MEAN"]
    std = row["STD"] if row["STD"] > 0 else 1
    line = mean

    prob_over = 1 - norm.cdf(line, mean, std)
    value = abs(prob_over - 0.5)

    if prob_over >= 0.57 and value >= 0.12 and p90 <= line + 8:
        send_alert(
            f"OVER PRA AUTO\n{player}\nLigne: {line}\nProba: {round(prob_over*100,1)}%"
        )
