# flowup_scraper.py

import time
import tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import (
    FLOWUP_LOGIN_URL,
    FLOWUP_USERNAME,
    FLOWUP_PASSWORD,
    # Остальные переменные можно добавить, если они понадобятся (например, пороговые значения)
)

class FlowUpScraper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Без графического интерфейса
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # Создаем временный каталог для данных пользователя
        tmp_dir = tempfile.mkdtemp()
        chrome_options.add_argument(f"--user-data-dir={tmp_dir}")
        self.driver = webdriver.Chrome(options=chrome_options)
    
    def login(self):
        self.driver.get(FLOWUP_LOGIN_URL)
        # Ожидаем появления полей логина и пароля
        email_input = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input#typeEmailX"))
        )
        password_input = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input#typePasswordX"))
        )
        email_input.send_keys(FLOWUP_USERNAME)
        password_input.send_keys(FLOWUP_PASSWORD)
        login_button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
        )
        login_button.click()
        WebDriverWait(self.driver, 20).until(EC.url_changes(FLOWUP_LOGIN_URL))
        time.sleep(2)
    
    def process_company_and_driver(self):
        report = []
        # 1. Нажимаем на элемент компании
        company_selector = "#ngb-panel-10-header > button > div > div.col-3.company-title > div.header-content.company-title"
        company_element = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, company_selector))
        )
        company_name = company_element.text.strip()
        report.append(f"Компания: {company_name}")
        # Клик по компании
        self.driver.execute_script("arguments[0].click();", company_element)
        time.sleep(2)
        
        # 2. Выбираем водителя
        driver_selector = "#ngb-panel-10 > div > app-drivers > div > table > tr.ng-star-inserted > td:nth-child(12) > div > img"
        driver_element = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, driver_selector))
        )
        # Здесь можно добавить клик, если требуется: 
        self.driver.execute_script("arguments[0].click();", driver_element)
        time.sleep(2)
        report.append("Выбран водитель (SELECT DRIVER)")
        
        # 3. Нажимаем кнопку "Start Transaction"
        start_selector = "#move-cont > div > button.mat-mdc-tooltip-trigger.action_btn.mdc-button.mdc-button--outlined.mat-mdc-outlined-button.mat-primary.mat-mdc-button-base.ng-star-inserted > span.mdc-button__label > img"
        start_button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, start_selector))
        )
        start_button.click()
        report.append("Нажата кнопка Start Transaction")
        time.sleep(2)
        
        # 4. Нажимаем кнопку "Check Logbook"
        check_selector = "#move-cont > div.flex > button:nth-child(10) > span.mdc-button__label > img"
        check_button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, check_selector))
        )
        check_button.click()
        report.append("Нажата кнопка Check Logbook")
        time.sleep(2)
        
        # 5. Считываем ошибки логбука
        errors_selector = "body > app-root > div > app-transaction > div > div.overlay.ng-star-inserted > div > app-all-driver-errors"
        try:
            errors_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, errors_selector))
            )
            errors_text = errors_element.text.strip()
            report.append(f"Ошибки логбука: {errors_text}")
        except Exception:
            report.append("Ошибки логбука не найдены")
        
        # 6. Считываем оставшееся время (таймеры)
        timers_selector = "body > app-root > div > app-transaction > div > div.transaction-content.ng-star-inserted > div.header > div:nth-child(6) > app-real-time-cyrcles"
        try:
            timers_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, timers_selector))
            )
            timers_text = timers_element.text.strip()
            report.append(f"Время водителя: {timers_text}")
        except Exception:
            report.append("Таймеры не найдены")
        
        # 7. Нажимаем кнопку "Finish Transaction"
        finish_selector = "#move-cont > div.flex > button.action_btn.mdc-button.mdc-button--outlined.mat-mdc-outlined-button.mat-unthemed.mat-mdc-button-base > span.mdc-button__label > img"
        finish_button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, finish_selector))
        )
        finish_button.click()
        report.append("Нажата кнопка Finish Transaction")
        time.sleep(2)
        
        return "\n".join(report)
    
    def generate_report(self):
        try:
            self.login()
            time.sleep(2)
            report = self.process_company_and_driver()
        except Exception as e:
            report = f"Общая ошибка: {e}"
        finally:
            self.driver.quit()
        return report

if __name__ == "__main__":
    scraper = FlowUpScraper()
    result = scraper.generate_report()
    print(result)