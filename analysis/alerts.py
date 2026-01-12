import json
from datetime import date
import requests
from pathlib import Path

STATE_FILE = Path("data_export/alerts_sent.json")

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}

def save_state(state):
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state))

def send_alert(bot_token, chat_id, player, line, prob, odds):
    state = load_state()
    today = str(date.today())

    key = f"{today}_{player}"
    if state.get(key):
        return False  # déjà envoyé

    msg = (
        f"🟢 OVER PRA — CONFIANCE A\n\n"
        f"Joueur : {player}\n"
        f"Ligne : {line}\n"
        f"Cote : {odds}\n"
        f"Probabilité : {round(prob*100,1)} %"
    )

    requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data={"chat_id": chat_id, "text": msg},
        timeout=5
    )

    state[key] = True
    save_state(state)
    return True
