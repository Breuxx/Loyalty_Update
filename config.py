# config.py

# URL для входа на платформу Flow-Up
FLOWUP_LOGIN_URL = "http://flow-up.com/login"

# Учётные данные для входа на Flow-Up
FLOWUP_USERNAME = "your_flowup_username"
FLOWUP_PASSWORD = "your_flowup_password"

# Telegram Bot Token и Chat ID, куда отправлять отчёты
TELEGRAM_BOT_TOKEN = "your_telegram_bot_token"
TELEGRAM_CHAT_ID = "your_telegram_chat_id"  # ID чата или пользователя, куда будет отправляться отчёт

# Пороговые значения таймеров (в секундах)
THRESHOLD_BREAK = 2 * 3600    # 2 часа
THRESHOLD_SHIFT = 2 * 3600    # 2 часа
THRESHOLD_CYCLE = 10 * 3600   # 10 часов

# Интервал обновления (например, каждые 60 секунд)
UPDATE_INTERVAL = 60
