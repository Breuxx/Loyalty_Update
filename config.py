# config.py

# URL для входа на платформу Flow-Up
FLOWUP_LOGIN_URL = "http://flow-up.com/login"

# Учётные данные для входа на Flow-Up
FLOWUP_USERNAME = "old_loyaltyeldservice@gmail.com"
FLOWUP_PASSWORD = "flow2024"

# Telegram Bot Token и Chat ID, куда отправлять отчёты
TELEGRAM_BOT_TOKEN = "7654501983:AAGi8L3LHBck1tlu4FVvRDeUfq0FgKzCWiA"
TELEGRAM_CHAT_ID = "-1002517831982"  # ID чата или пользователя, куда будет отправляться отчёт

# Пороговые значения таймеров (в секундах)
THRESHOLD_BREAK = 2 * 3600    # 2 часа
THRESHOLD_SHIFT = 2 * 3600    # 2 часа
THRESHOLD_CYCLE = 10 * 3600   # 10 часов

# Интервал обновления (например, каждые 60 секунд)
UPDATE_INTERVAL = 120
