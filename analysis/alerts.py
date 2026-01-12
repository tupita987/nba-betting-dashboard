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

def send_alert(
    bot_token,
    chat_id,
    player,
    matchup,
    home,
    b2b,
    model_line,
    book_line,
    odds,
    prob
):
    state = _load_state()
    today = str(date.today())
    key = f"{today}_{player}"

    # Anti-spam : 1 alerte / joueur / jour
    if state.get(key):
        return False

    message = (
        "🚨🔥 *OVER PRA DÉTECTÉ* 🔥🚨\n\n"
        f"👤 *Joueur* : {player}\n"
        f"🏀 *Match* : {matchup}\n"
        f"🏠 *Domicile* : {'Oui' if home else 'Non'} | "
        f"🔁 *B2B* : {'Oui' if b2b else 'Non'}\n\n"
        f"📊 *PRA Modèle* : {model_line}\n"
        f"🎯 *Ligne Book* : {book_line} @ {odds}\n\n"
        f"📈 *Probabilité Over* : {round(prob*100,1)} %\n"
        f"💎 *Confiance* : A\n\n"
        "⚠️ *Value détectée — opportunité rare*"
    )

        try:
        r = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown"
            },
            timeout=5
        )

        if r.status_code != 200:
            return False

    except Exception:
        return False

    state[key] = True
    _save_state(state)
    return True

