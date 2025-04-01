import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from telegram import Bot

# Получение переменных окружения
FLOW_LOGIN_URL = os.environ.get("FLOW_LOGIN_URL", "https://flow-up.com/login")
FLOW_USERNAME = os.environ.get("FLOW_USERNAME")
FLOW_PASSWORD = os.environ.get("FLOW_PASSWORD")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 1200))  # 20 минут

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    # Указываем путь к бинарнику Chrome/Chromium и chromedriver из переменных окружения
    chrome_options.binary_location = os.environ.get("CHROME_BIN", "/usr/bin/chromium")
    driver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")
    driver = webdriver.Chrome(executable_path=driver_path, options=chrome_options)
    return driver

def login_flow(driver):
    driver.get(FLOW_LOGIN_URL)
    time.sleep(3)
    try:
        username_input = driver.find_element(By.ID, "username")
        password_input = driver.find_element(By.ID, "password")
        login_button = driver.find_element(By.ID, "loginBtn")
    except Exception as e:
        print("Форма логина не найдена, возможно, уже авторизованы:", e)
        return
    username_input.send_keys(FLOW_USERNAME)
    password_input.send_keys(FLOW_PASSWORD)
    login_button.click()
    time.sleep(5)

def process_driver_log(driver):
    report = ""
    try:
        start_transaction_btn = driver.find_element(By.XPATH, "//span[contains(., 'Start Transaction')]")
        start_transaction_btn.click()
        time.sleep(2)
        
        check_logbook_btn = driver.find_element(By.XPATH, "//span[contains(., 'Check logBook')]")
        check_logbook_btn.click()
        time.sleep(3)
        
        error_elements = driver.find_elements(By.CSS_SELECTOR, "div.events-short-table-labels-label")
        if error_elements:
            for err in error_elements:
                color = driver.execute_script("return window.getComputedStyle(arguments[0]).color;", err)
                if "255, 0, 0" in color:
                    report += f"CRITICAL ERROR: {err.text}\n"
                else:
                    report += f"Notice: {err.text}\n"
        else:
            report += "Ошибок не обнаружено.\n"
        
        timer_elements = driver.find_elements(By.CSS_SELECTOR, "tspan.ng-star-inserted")
        if timer_elements and len(timer_elements) >= 3:
            break_time = timer_elements[0].text
            shift_time = timer_elements[1].text
            cycle_time = timer_elements[2].text
            report += f"Break remaining: {break_time}\n"
            report += f"Shift remaining: {shift_time}\n"
            report += f"Cycle remaining: {cycle_time}\n"
            
            if break_time < "2:00":
                report += "Напоминание: Break менее 2 часов!\n"
            if shift_time < "2:00":
                report += "Напоминание: Shift менее 2 часов!\n"
            if cycle_time < "10:00":
                report += "Напоминание: Cycle менее 10 часов!\n"
        else:
            report += "Таймеры не обнаружены.\n"
        
        finish_transaction_btn = driver.find_element(By.XPATH, "//span[contains(., 'Finish transaction') or contains(., 'Finish')]")
        finish_transaction_btn.click()
        time.sleep(1)
    except Exception as e:
        report += f"Ошибка при обработке лога водителя: {e}\n"
    return report

def process_company(driver):
    company_report = ""
    try:
        driver_elements = driver.find_elements(By.CSS_SELECTOR, "td")
        if not driver_elements:
            company_report += "Нет водителей в этой компании.\n"
        else:
            company_report += f"Найдено водителей: {len(driver_elements)}\n"
            for drv in driver_elements:
                driver_name = drv.text.strip()
                drv.click()
                time.sleep(2)
                driver_report = process_driver_log(driver)
                company_report += f"Отчёт по водителю {driver_name}:\n{driver_report}\n"
                driver.back()
                time.sleep(2)
    except Exception as e:
        company_report += f"Ошибка при обработке компании: {e}\n"
    return company_report

def process_all_companies(driver):
    full_report = ""
    try:
        company_elements = driver.find_elements(By.CSS_SELECTOR, "div.header-content.company-title")
        if not company_elements:
            full_report += "Нет доступных компаний.\n"
        else:
            full_report += f"Найдено компаний: {len(company_elements)}\n"
            for comp in company_elements:
                comp_name = comp.text.strip()
                comp.click()
                time.sleep(3)
                comp_report = process_company(driver)
                full_report += f"Компания: {comp_name}\n{comp_report}\n"
                driver.back()
                time.sleep(2)
    except Exception as e:
        full_report += f"Ошибка при обработке компаний: {e}\n"
    return full_report

def send_report(report_text):
    try:
        bot = Bot(token=TELEGRAM_TOKEN)
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=report_text)
    except Exception as e:
        print("Ошибка при отправке отчёта в Telegram:", e)

def main():
    driver = setup_driver()
    login_flow(driver)
    while True:
        report = process_all_companies(driver)
        send_report(report)
        print("Отчёт отправлен, ожидание следующего цикла...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()