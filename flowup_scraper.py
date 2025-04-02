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
        # Для отладки можно вывести HTML страницы:
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
        try:
            WebDriverWait(self.driver, 20).until(EC.url_changes(FLOWUP_LOGIN_URL))
        except Exception:
            # Если URL не меняется, можно добавить ожидание появления другого элемента,
            # характерного для авторизованной страницы.
            pass

    def get_company_identifiers(self):
        """
        Находит все элементы компаний по селектору и возвращает список очищённых названий.
        """
        try:
            companies = WebDriverWait(self.driver, 20).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.company-title"))
            )
        except Exception as e:
            print("Отладка: Элементы компаний не найдены:", e)
            companies = []
        print(f"Отладка: Найдено компаний: {len(companies)}")
        identifiers = []
        for comp in companies:
            text = comp.text.strip()
            # Если в тексте встречается лишний префикс (например, "Company"), удаляем его.
            if text.lower().startswith("company"):
                text = text[len("company"):].strip()
            if text:
                identifiers.append(text)
        return identifiers

    def open_company(self, company_identifier):
        """
        Находит и кликает по элементу компании с текстом company_identifier,
        используя XPath с normalize-space().
        Повторяет попытку до 3 раз.
        """
        xpath = f"//div[contains(@class, 'company-title') and normalize-space(.)='{company_identifier}']"
        for attempt in range(3):
            try:
                company_element = WebDriverWait(self.driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )
                # Прокручиваем элемент в область видимости
                self.driver.execute_script("arguments[0].scrollIntoView(true);", company_element)
                self.driver.execute_script("arguments[0].click();", company_element)
                time.sleep(2)
                return True
            except Exception as e:
                print(f"Отладка: Попытка {attempt+1} открыть компанию '{company_identifier}' не удалась: {e}")
                time.sleep(1)
        return False

    def get_drivers(self):
        """
        Возвращает список элементов водителей.
        Здесь используется селектор для ячеек <td> с атрибутом _ngcontent-ng-c3802590250.
        Возможно, потребуется уточнить селектор в зависимости от структуры страницы.
        """
        try:
            # Можно добавить ожидание появления хотя бы одного водителя, если они должны быть.
            drivers = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "td[_ngcontent-ng-c3802590250]"))
            )
        except Exception as e:
            print("Отладка: Водители не найдены на странице компании:", e)
            drivers = []
        return drivers

    def process_company(self, company_identifier, companies_page_url):
        if not self.open_company(company_identifier):
            return [f"Не удалось открыть компанию '{company_identifier}' после нескольких попыток."]
        drivers = self.get_drivers()
        print(f"Отладка: Для компании '{company_identifier}' найдено водителей: {len(drivers)}")
        report_lines = []
        if not drivers:
            report_lines.append("В компании нет водителей.")
        else:
            for driver in drivers:
                driver_name = driver.text.strip()
                if driver_name:
                    report_lines.append(f"Обработка водителя: {driver_name}")
                    driver_report = self.process_driver(driver_name)
                    report_lines.extend(driver_report)
        # После обработки возвращаемся на страницу списка компаний
        self.driver.get(companies_page_url)
        time.sleep(2)
        return report_lines

    def process_driver(self, driver_name):
        report = []
        try:
            start_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Start Transaction')]"))
            )
            start_button.click()
            time.sleep(2)
        except Exception as e:
            report.append(f"Ошибка при нажатии Start Transaction для {driver_name}: {e}")
            return report
        try:
            check_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Check Logbook')]"))
            )
            check_button.click()
            time.sleep(2)
        except Exception as e:
            report.append(f"Ошибка при нажатии Check Logbook для {driver_name}: {e}")
            return report

        red_errors = self.driver.find_elements(By.CSS_SELECTOR, ".error.red")
        white_errors = self.driver.find_elements(By.CSS_SELECTOR, ".error.white")
        if red_errors:
            for err in red_errors:
                error_text = err.text.strip()
                report.append(f"Критичная ошибка: {error_text}")
        else:
            report.append("Критичных ошибок не обнаружено.")
        if white_errors:
            for err in white_errors:
                error_text = err.text.strip()
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
            report.append(f"Ошибка при чтении таймеров для {driver_name}: {e}")
        try:
            finish_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Finish Transaction')]"))
            )
            finish_button.click()
            time.sleep(2)
        except Exception as e:
            report.append(f"Ошибка при завершении транзакции для {driver_name}: {e}")
        return report

    def generate_report(self):
        final_report = []
        try:
            self.login()
            companies_page_url = self.driver.current_url
            company_identifiers = self.get_company_identifiers()
            if not company_identifiers:
                final_report.append("Нет компаний для обработки.")
            else:
                final_report.append(f"Найдено компаний: {len(company_identifiers)}")
                for identifier in company_identifiers:
                    final_report.append(f"\nКомпания: {identifier}")
                    comp_report = self.process_company(identifier, companies_page_url)
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