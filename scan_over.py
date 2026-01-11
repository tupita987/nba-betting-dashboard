import os
import requests

print("SCAN START")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

print("TOKEN OK:", bool(BOT_TOKEN))
print("CHAT OK:", bool(CHAT_ID))

if not BOT_TOKEN or not CHAT_ID:
    raise RuntimeError("Secrets Telegram manquants")

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
resp = requests.post(url, data={
    "chat_id": CHAT_ID,
    "text": "🟢 Scan GitHub Actions OK"
})

print("STATUS:", resp.status_code)
print("RESPONSE:", resp.text)

print("SCAN END")
