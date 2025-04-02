# main.py

import time
from flowup_scraper import FlowUpScraper
from telegram_bot import send_report
from config import UPDATE_INTERVAL

def run_cycle():
    scraper = FlowUpScraper()
    report = scraper.generate_report()
    print("Отчёт сформирован:")
    print(report)
    send_report(report)

if __name__ == "__main__":
    while True:
        print("Запуск цикла проверки...")
        run_cycle()
        print(f"Ожидание {UPDATE_INTERVAL} секунд до следующего обновления...")
        time.sleep(UPDATE_INTERVAL)