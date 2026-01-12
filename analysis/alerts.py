import json
import requests
from datetime import date
from pathlib import Path

STATE_FILE = Path("data_export/alerts_sent.json")

def _load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}

def _save_state(state):
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state))

def send_alert(bot_token, chat_id, message):
    """
    Envoi simple Telegram (son activé par défaut)
    """
    requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        },
        timeout=5
    )

def send_combo_alert(bot_token, chat_id, combo):
    """
    Envoie UN combiné intelligent par jour (anti-spam)
    """
    state = _load_state()
    today = str(date.today())
    key = f"{today}_COMBO"

    if state.get(key):
        return False

    msg = (
        "🚨🔥 *COMBINÉ INTELLIGENT NBA* 🔥🚨\n\n"
        "🧠 *OVER A uniquement — ultra filtré*\n\n"
    )

    for i, p in enumerate(combo["players"], start=1):
        msg += f"{i}️⃣ *{p}* — OVER PRA\n"

    msg += (
        f"\n📈 *Probabilité combinée* : {round(combo['prob']*100,1)} %\n"
        f"💰 *Cote combinée* : {combo['odds']}\n\n"
        "⚠️ *Matchs différents — edge réel détecté*"
    )

    send_alert(bot_token, chat_id, msg)

    state[key] = True
    _save_state(state)
    return True
