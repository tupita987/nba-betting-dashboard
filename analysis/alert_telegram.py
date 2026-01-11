import requests

BOT_TOKEN = "TON_TOKEN_ICI"
CHAT_ID = "TON_CHAT_ID_ICI"

def send_alert(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except:
        pass