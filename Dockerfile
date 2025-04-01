# Используем официальный образ Python 3.12 на базе slim
FROM python:3.12-slim

# Обновляем систему и устанавливаем зависимости для Chrome/Chromium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Chromium и chromedriver
RUN apt-get update && apt-get install -y chromium chromium-driver

# Устанавливаем переменные окружения для путей
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Копируем файл зависимостей
WORKDIR /app
COPY requirements.txt /app/requirements.txt

# Устанавливаем зависимости
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Копируем все файлы проекта в контейнер
COPY . /app

# Команда для запуска приложения
CMD ["python", "main.py"]
