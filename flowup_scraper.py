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
        chrome_options.add_argument("--headless")  # Без графического интерфейса
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # Создаем временный каталог для пользовательских данных
        tmp_dir = tempfile.mkdtemp()
        chrome_options.add_argument(f"--user-data-dir={tmp_dir}")
        self.driver = webdriver.Chrome(options=chrome_options)
    
    def login(self):
        self.driver.get(FLOWUP_LOGIN_URL)
        # Ждем появления полей логина и пароля
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
    
    def process_company_and_driver(self):
        report = []
        # 1. Находим компанию по указанному селектору и получаем её имя
        company_selector = "#ngb-panel-210-header > button > div > div.col-3.company-title > div.header-label"
        company_element = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, company_selector))
        )
        company_name = company_element.text.strip()
        report.append(f"Компания: {company_name}")
        self.driver.execute_script("arguments[0].click();", company_element)
        time.sleep(2)
        
        # 2. Находим первого водителя по селектору
        driver_selector = "#ngb-panel-210 > div > app-drivers > div > table > tr.ng-star-inserted > td:nth-child(1)"
        driver_element = WebDriverWait(self.driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, driver_selector))
        )
        driver_name = driver_element.text.strip()
        report.append(f"Водитель: {driver_name}")
        time.sleep(2)
        
        # 3. Нажимаем кнопку "Start Transaction"
        start_transaction_selector = "#move-cont > div > button.mat-mdc-tooltip-trigger.action_btn.mdc-button.mdc-button--outlined.mat-mdc-outlined-button.mat-primary.mat-mdc-button-base.ng-star-inserted > span.mat-mdc-focus-indicator"
        start_button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, start_transaction_selector))
        )
        start_button.click()
        report.append("Нажата кнопка Start Transaction")
        time.sleep(2)
        
        # 4. Нажимаем кнопку "Check Logbook"
        check_logbook_selector = "#move-cont > div.flex > button:nth-child(10) > span.mat-mdc-focus-indicator"
        check_logbook_button = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, check_logbook_selector))
        )
        check_logbook_button.click()
        report.append("Нажата кнопка Check Logbook")
        time.sleep(2)
        
        # 5. Считываем ошибки логбука
        errors_selector = "body > app-root > div > app-transaction > div > div.overlay.ng-star-inserted > div"
        try:
            errors_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, errors_selector))
            )
            errors_text = errors_element.text.strip()
            report.append(f"Ошибки логбука: {errors_text}")
        except Exception:
            report.append("Ошибки логбука не найдены")
        
        # 6. Считываем время водителя (таймеры)
        timers_selector = "body > app-root > div > app-transaction > div > div.transaction-content.ng-star-inserted > div.header > div:nth-child(6) > div > label"
        try:
            timers_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, timers_selector))
            )
            timers_text = timers_element.text.strip()
            report.append(f"Время водителя: {timers_text}")
        except Exception:
            report.append("Таймеры не найдены")
        
        # 7. Нажимаем кнопку "Finish Transaction"
        finish_selector = "#move-cont > div.flex > button.action_btn.mdc-button.mdc-button--outlined.mat-mdc-outlined-button.mat-unthemed.mat-mdc-button-base > span.mat-mdc-focus-indicator"
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
            # Если нужно, подождать загрузку списка компаний после входа
            time.sleep(2)
            report = self.process_company_and_driver()
        except Exception as e:
            report = f"Общая ошибка: {e}"
        finally:
            self.driver.quit()
        return report

if __name__ == "__main__":
    scraper = FlowUpScraper()
    report = scraper.generate_report()
    print(report)