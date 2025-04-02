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
    THRESHOLD_BREAK,
    THRESHOLD_SHIFT,
    THRESHOLD_CYCLE
)

class FlowUpScraper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Запуск без графического интерфейса
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        # Использование временного каталога для данных пользователя.
        tmp_dir = tempfile.mkdtemp()
        chrome_options.add_argument(f"--user-data-dir={tmp_dir}")
        
        self.driver = webdriver.Chrome(options=chrome_options)
    
    def login(self):
        self.driver.get(FLOWUP_LOGIN_URL)
        
        # Для отладки можно раскомментировать следующую строку,
        # чтобы увидеть HTML-код страницы входа:
        # print(self.driver.page_source)
        
        try:
            email_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input#typeEmailX"))
            )
        except Exception as e:
            raise Exception(f"Поле для логина не найдено: {e}")

        try:
            password_input = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input#typePasswordX"))
            )
        except Exception as e:
            raise Exception(f"Поле для пароля не найдено: {e}")

        email_input.send_keys(FLOWUP_USERNAME)
        password_input.send_keys(FLOWUP_PASSWORD)
        
        try:
            login_button = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
            )
            login_button.click()
        except Exception as e:
            raise Exception(f"Кнопка входа не найдена или не кликабельна: {e}")
        
        # Ожидаем изменения URL после входа или появления индикатора авторизации
        try:
            WebDriverWait(self.driver, 20).until(EC.url_changes(FLOWUP_LOGIN_URL))
        except Exception:
            # Если URL не меняется, можно добавить ожидание появления элемента,
            # характерного для авторизованной страницы.
            pass

    def get_companies(self):
        # Если на странице компаний есть контейнер, можно ожидать его появления.
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".company-container"))
            )
        except Exception as e:
            print("Предупреждение: Контейнер компаний не найден. Возможно, селектор нужно изменить.", e)
        
        companies = self.driver.find_elements(By.CSS_SELECTOR, ".company-item")
        print(f"Отладка: Найдено компаний: {len(companies)}")
        if len(companies) == 0:
            # Выводим часть HTML страницы для отладки
            html_snippet = self.driver.page_source[:1000]
            print("Отладка: HTML страницы компаний (первые 1000 символов):")
            print(html_snippet)
        company_links = [company.get_attribute("href") for company in companies]
        return company_links
    
    def process_company(self, company_url):
        self.driver.get(company_url)
        time.sleep(2)
        
        drivers = self.driver.find_elements(By.CSS_SELECTOR, ".driver-item")
        print(f"Отладка: По компании {company_url} найдено водителей: {len(drivers)}")
        report_lines = []
        if not drivers:
            report_lines.append("В компании нет водителей.")
            return report_lines
        
        for driver in drivers:
            driver_name = driver.text
            driver.click()  # Заходим в профиль водителя
            time.sleep(2)
            report_lines.append(f"Обработка водителя: {driver_name}")
            driver_report = self.process_driver()
            report_lines.extend(driver_report)
            self.driver.back()
            time.sleep(2)
        return report_lines

    def process_driver(self):
        report = []
        try:
            start_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Start Transaction')]"))
            )
            start_button.click()
            time.sleep(2)
        except Exception as e:
            report.append(f"Ошибка при нажатии Start Transaction: {e}")
            return report
        
        try:
            check_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Check Logbook')]"))
            )
            check_button.click()
            time.sleep(2)
        except Exception as e:
            report.append(f"Ошибка при нажатии Check Logbook: {e}")
            return report

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
        
        try:
            break_timer = int(self.driver.find_element(By.ID, "break-timer").text)
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
        
        try:
            finish_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Finish Transaction')]"))
            )
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

if __name__ == "__main__":
    scraper = FlowUpScraper()
    report = scraper.generate_report()
    print(report)