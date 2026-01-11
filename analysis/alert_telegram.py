import requests

BOT_TOKEN = "8414100374: AAGV1DBabq1w8JYzYEltG
-vuG2P10K4mNcc"
CHAT_ID = "6139600150"

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