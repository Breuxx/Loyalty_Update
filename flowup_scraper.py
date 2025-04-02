# flowup_scraper.py

import time
import tempfile
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from config import (
    FLOWUP_LOGIN_URL,
    FLOWUP_USERNAME,
    FLOWUP_PASSWORD,
    THRESHOLD_BREAK,
    THRESHOLD_SHIFT,
    THRESHOLD_CYCLE
)

class FlowUpScraper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # запускаем без GUI
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Вариант 1: Используем уникальный каталог для данных пользователя
        tmp_dir = tempfile.mkdtemp()
        chrome_options.add_argument(f"--user-data-dir={tmp_dir}")
        
        # Если всё ещё возникает ошибка, можно попробовать убрать аргумент --user-data-dir:
        # chrome_options.arguments = [arg for arg in chrome_options.arguments if "--user-data-dir" not in arg]
        
        self.driver = webdriver.Chrome(options=chrome_options)
    
    def login(self):
        self.driver.get(FLOWUP_LOGIN_URL)
        time.sleep(2)  # подождать загрузку страницы

        # Пример: Найти поля логина и пароля и заполнить их
        username_input = self.driver.find_element(By.NAME, "username")
        password_input = self.driver.find_element(By.NAME, "password")
        username_input.send_keys(FLOWUP_USERNAME)
        password_input.send_keys(FLOWUP_PASSWORD)
        
        # Найти и нажать кнопку входа
        login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()
        time.sleep(3)  # ожидание авторизации
    
    def get_companies(self):
        # Предполагается, что после входа отображается список компаний
        companies = self.driver.find_elements(By.CSS_SELECTOR, ".company-item")
        company_links = [company.get_attribute("href") for company in companies]
        return company_links
    
    def process_company(self, company_url):
        self.driver.get(company_url)
        time.sleep(2)
        
        # Находим список водителей в компании
        drivers = self.driver.find_elements(By.CSS_SELECTOR, ".driver-item")
        report_lines = []
        if not drivers:
            report_lines.append("В компании нет водителей.")
            return report_lines
        
        for driver in drivers:
            driver_name = driver.text
            driver.click()  # заходим в профиль водителя
            time.sleep(2)
            report_lines.append(f"Обработка водителя: {driver_name}")
            driver_report = self.process_driver()
            report_lines.extend(driver_report)
            # Возвращаемся к списку водителей
            self.driver.back()
            time.sleep(2)
        return report_lines

    def process_driver(self):
        report = []
        # 1. Нажать Start Transaction
        try:
            start_button = self.driver.find_element(By.XPATH, "//button[contains(text(),'Start Transaction')]")
            start_button.click()
            time.sleep(2)
        except Exception as e:
            report.append(f"Ошибка при нажатии Start Transaction: {e}")
            return report
        
        # 2. Нажать Check Logbook
        try:
            check_button = self.driver.find_element(By.XPATH, "//button[contains(text(),'Check Logbook')]")
            check_button.click()
            time.sleep(2)
        except Exception as e:
            report.append(f"Ошибка при нажатии Check Logbook: {e}")
            return report

        # 3. Собрать ошибки
        red_errors = self.driver.find_elements(By.CSS_SELECTOR, ".error.red")
        white_errors = self.driver.find_elements(By.CSS_SELECTOR, ".error.white")
        
        if red_errors:
            for err in red_errors:
                error_text = err.text
                report.append(f"Критичная ошибка: {error_text}")
        else:
            report.append("Критичных ошибок не обнаружено.")
        
        if white_errors:
            for err in white_errors:
                error_text = err.text
                report.append(f"Не критичная ошибка: {error_text}")
        else:
            report.append("Некритичных ошибок не обнаружено.")
        
        # 4. Чтение таймеров (пример)
        try:
            break_timer = int(self.driver.find_element(By.ID, "break-timer").text)  # значение в секундах
            shift_timer = int(self.driver.find_element(By.ID, "shift-timer").text)
            cycle_timer = int(self.driver.find_element(By.ID, "cycle-timer").text)
            
            if break_timer < THRESHOLD_BREAK:
                report.append(f"Внимание: оставшееся время Break {break_timer//3600} ч.")
            if shift_timer < THRESHOLD_SHIFT:
                report.append(f"Внимание: оставшееся время Shift {shift_timer//3600} ч.")
            if cycle_timer < THRESHOLD_CYCLE:
                report.append(f"Внимание: оставшееся время Cycle {cycle_timer//3600} ч.")
        except Exception as e:
            report.append(f"Ошибка при чтении таймеров: {e}")
        
        # 5. Завершить транзакцию
        try:
            finish_button = self.driver.find_element(By.XPATH, "//button[contains(text(),'Finish Transaction')]")
            finish_button.click()
            time.sleep(2)
        except Exception as e:
            report.append(f"Ошибка при завершении транзакции: {e}")
        
        return report

    def generate_report(self):
        final_report = []
        try:
            self.login()
            companies = self.get_companies()
            if not companies:
                final_report.append("Нет компаний для обработки.")
            else:
                final_report.append(f"Найдено компаний: {len(companies)}")
                for comp_url in companies:
                    final_report.append(f"\nОбработка компании: {comp_url}")
                    comp_report = self.process_company(comp_url)
                    final_report.extend(comp_report)
        except Exception as e:
            final_report.append(f"Общая ошибка: {e}")
        finally:
            self.driver.quit()
        return "\n".join(final_report)

# Пример использования:
if __name__ == "__main__":
    scraper = FlowUpScraper()
    report = scraper.generate_report()
    print(report)