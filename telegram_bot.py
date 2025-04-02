# telegram_bot.py

import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_report(report_text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": report_text,
        "parse_mode": "Markdown"
    }
    response = requests.post(url, data=payload)
    return response.json()

# Пример использования:
if __name__ == "__main__":
    sample_report = "Это тестовый отчёт."
    print(send_report(sample_report))
