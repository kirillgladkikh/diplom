# test_pagination.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re


def test_pagination():
    print("Запуск теста пагинации...")

    # Настройка драйвера
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # Загружаем страницу
        driver.get("https://goldapple.ru/parfjumerija")
        print("Страница загружена")

        # Ждем загрузки пагинации
        wait = WebDriverWait(driver, 10)
        pagination = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul._ga-plp-pagination_1ert2_1"))
        )

        print("\n" + "=" * 60)
        print("HTML пагинации:")
        print("=" * 60)
        print(pagination.get_attribute('outerHTML'))

        print("\n" + "=" * 60)
        print("Текст пагинации:")
        print("=" * 60)
        print(pagination.text)

        print("\n" + "=" * 60)
        print("Найденные числа:")
        print("=" * 60)
        numbers = re.findall(r'\d+', pagination.text)
        print(f"Все числа: {numbers}")

        if numbers:
            last_page = max(int(n) for n in numbers)
            print(f"Максимальное число: {last_page}")

    except Exception as e:
        print(f"Ошибка: {e}")

    finally:
        driver.quit()
        print("\nДрайвер закрыт")


if __name__ == "__main__":
    test_pagination()