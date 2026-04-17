"""Парсинг детальной информации о товаре"""

import os
import time
import random
import re
import csv
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from src.config import (
    REQUEST_DELAY_MIN, REQUEST_DELAY_MAX, RETRY_COUNT,
    SELECTORS_PDP, OUTPUT_FILENAME, SELECTORS_REVIEW
)
from src.product import Product
from src.utils import parse_price


class Parser:
    """Парсинг детальной информации о продуктах"""

    def __init__(self, input_filename: str = OUTPUT_FILENAME, data_dir: str = "data"):
        self.input_filename = input_filename
        self.input_path = os.path.join(data_dir, input_filename)
        self.driver: Optional[webdriver.Chrome] = None

    def _init_driver(self) -> webdriver.Chrome:
        """Инициализация драйвера"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--log-level=3")
        chrome_options.set_capability("pageLoadStrategy", "eager")

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(30)
        return driver

    def _random_delay(self) -> None:
        """Случайная задержка"""
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        time.sleep(delay)

    def restart_driver(self) -> None:
        """Перезапускает драйвер"""
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass
        self.driver = self._init_driver()

    def _safe_get(self, url: str, retries: int = RETRY_COUNT) -> bool:
        """Безопасное получение страницы с повторными попытками"""
        for attempt in range(retries):
            try:
                if self.driver is None:
                    self.driver = self._init_driver()

                self.driver.get(url)

                # Ждём загрузки body
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                # Дополнительная задержка для динамического контента (3 секунды)
                time.sleep(3)

                # Прокручиваем вниз, чтобы подгрузить динамические блоки
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(3)

                # Прокручиваем обратно вверх
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(3)

                # Ждем загрузки вкладок (после прокруток, чтобы контент точно подгрузился)
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='ga-tabs-tab']"))
                    )
                    print(f"  📑 Вкладки загружены")
                except Exception as e:
                    print(f"  ⚠️ Вкладки не найдены: {e}")

                return True
            except (TimeoutException, Exception) as e:
                print(f"⚠️ Попытка {attempt + 1}/{retries} не удалась: {e}")
                if attempt == retries - 1:
                    return False
                self._random_delay()
                self.restart_driver()
        return False

    def debug_save_page_source(self, filename: str = "debug_page.html") -> None:
        """Сохраняет текущий HTML страницы для отладки"""
        try:
            if self.driver:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                print(f"💾 HTML страницы сохранён в {filename}")
                print(f"   Размер файла: {len(self.driver.page_source)} символов")
        except Exception as e:
            print(f"⚠️ Ошибка при сохранении HTML: {e}")

    def _get_text(self, selectors, default: str = "") -> str:
        """Пытается получить текст по одному из CSS селекторов"""
        if isinstance(selectors, str):
            selectors = [selectors]

        for selector in selectors:
            try:
                if self.driver is None:
                    return default
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text:
                    return text
            except NoSuchElementException:
                continue
        return default

    def _get_product_name(self) -> str:
        """Получает название продукта из h1"""
        try:
            if self.driver is None:
                return ""
            h1 = self.driver.find_element(By.CSS_SELECTOR, "h1")
            return h1.text.strip()
        except Exception as e:
            print(f"⚠️ Не удалось получить название: {e}")
            return ""

    def _get_price(self) -> str:
        """Получает цену продукта"""
        try:
            if self.driver is None:
                return ""

            price = self._get_text(SELECTORS_PDP["product_price"])
            if not price:
                return ""

            # Оставляем только цифры, точки и запятые (убираем пробелы, валюту и другие символы)
            price_clean = re.sub(r'[^\d.,]', '', price).strip()

            return price_clean if price_clean else price

        except Exception as e:
            print(f"⚠️ Не удалось получить цену: {e}")
            return ""

    def _get_rating_from_review_page(self, product_url: str) -> str:
        """
        Переходит на страницу отзывов и получает рейтинг товара.
        URL отзывов формируется: /review/product/{product_id}
        """
        try:
            # Извлекаем ID продукта из URL
            # URL вида: https://goldapple.ru/19000241264-rose-intense
            product_slug = product_url.split('/')[-1]
            product_id = product_slug.split('-')[0]  # Берём первую часть до дефиса

            # Формируем URL страницы отзывов
            review_url = f"https://goldapple.ru/review/product/{product_id}"
            print(f"  📝 Переход на страницу отзывов: {review_url}")

            # Загружаем страницу отзывов
            self.driver.get(review_url)
            time.sleep(10)  # Небольшая задержка для загрузки

            # Ищем рейтинг по селекторам из конфига
            for selector in SELECTORS_REVIEW["product_rating"]:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    rating = element.text.strip()
                    if rating and re.match(r'^\d+(\.\d+)?$', rating):
                        print(f"  ✅ Найден рейтинг на странице отзывов: {rating}")
                        return rating
                except NoSuchElementException:
                    continue

            print(f"  ⚠️ Рейтинг не найден на странице отзывов")
            return ""

        except Exception as e:
            print(f"  ⚠️ Ошибка при получении рейтинга со страницы отзывов: {e}")
            return ""

    def _get_instructions(self) -> str:
        """Получает инструкцию по применению из вкладки 'Применение'"""
        try:
            if self.driver is None:
                return "нет"

            # Кликаем по вкладке "Применение"
            try:
                apply_tab = self.driver.find_element(
                    By.XPATH,
                    "//button[contains(@class, 'ga-tabs-tab')]//div[contains(text(), 'Применение')]"
                )
                apply_tab.click()
                time.sleep(2)
                print(f"  🔘 Кликнули по вкладке 'Применение'")
            except Exception as e:
                print(f"  ⚠️ Вкладка 'Применение' отсутствует на странице")
                return "нет"

            # Получаем весь HTML страницы и ищем блок Применения
            page_source = self.driver.page_source

            # Ищем паттерн: text="Применение" и следующий за ним wysiwyg
            import re
            pattern = r'text="Применение".*?<div[^>]*class="[^"]*_ga-pdp-wysiwyg[^"]*"[^>]*>(.*?)</div>'
            match = re.search(pattern, page_source, re.DOTALL)

            if match:
                instructions = re.sub(r'<[^>]+>', '', match.group(1)).strip()
                instructions = re.sub(r'\s+', ' ', instructions)
                if instructions:
                    print(f"  📝 Найдена инструкция: {instructions[:50]}...")
                    return instructions

            print(f"  ❌ Инструкция не найдена")
            return "нет"

        except Exception as e:
            print(f"  ❌ Ошибка при получении инструкции: {e}")
            return "нет"

    # def _get_country(self) -> str:
    #     """Получает страну-производитель - комбинированный подход"""
    #     try:
    #         if self.driver is None:
    #             return ""
    #
    #         # Кликаем по вкладке
    #         try:
    #             additional_tab = self.driver.find_element(
    #                 By.XPATH,
    #                 "//button[contains(@class, 'ga-tabs-tab')]//div[contains(text(), 'Дополнительная информация')]"
    #             )
    #             additional_tab.click()
    #             time.sleep(2)
    #             print(f"  🔘 Кликнули по вкладке 'Дополнительная информация'")
    #         except Exception as e:
    #             print(f"  ⚠️ Не удалось кликнуть вкладку: {e}")
    #
    #         # Получаем весь блок
    #         container = self.driver.find_element(
    #             By.XPATH,
    #             "//div[contains(@class, 'wysiwyg') and contains(text(), 'страна происхождения')]"
    #         )
    #
    #         # Способ 1: Через innerHTML и <br>
    #         inner_html = container.get_attribute('innerHTML')
    #         import re
    #         parts = re.split(r'<br\s*/?>', inner_html)
    #
    #         for i, part in enumerate(parts):
    #             if 'страна происхождения' in part:
    #                 if i + 1 < len(parts):
    #                     country = re.sub(r'<[^>]+>', '', parts[i + 1]).strip()
    #                     if country:
    #                         print(f"  🌍 Найдена страна (через <br>): {country}")
    #                         return country
    #                 break
    #
    #         # Способ 2: Если не сработало, пробуем через текст и переносы строк
    #         full_text = container.text
    #         lines = full_text.split('\n')
    #         for i, line in enumerate(lines):
    #             if 'страна происхождения' in line.lower():
    #                 for j in range(i + 1, len(lines)):
    #                     if lines[j].strip():
    #                         country = lines[j].strip()
    #                         print(f"  🌍 Найдена страна (через text): {country}")
    #                         return country
    #                         break
    #                 break
    #
    #     except Exception as e:
    #         print(f"  ⚠️ Страна не найдена: {e}")
    #
    #     return ""

    def _get_country(self) -> str:
        """Получает страну-производитель через regex"""
        try:
            if self.driver is None:
                return ""

            # Кликаем по вкладке
            try:
                additional_tab = self.driver.find_element(
                    By.XPATH,
                    "//button[contains(@class, 'ga-tabs-tab')]//div[contains(text(), 'Дополнительная информация')]"
                )
                additional_tab.click()
                time.sleep(2)
                print(f"  🔘 Кликнули по вкладке 'Дополнительная информация'")
            except Exception as e:
                print(f"  ⚠️ Не удалось кликнуть вкладку: {e}")
                return ""

            # Получаем HTML и ищем страну
            page_source = self.driver.page_source
            import re

            # Ищем паттерн: страна происхождения<br>СТРАНА
            pattern = r'страна происхождения<br>(.*?)<br'
            match = re.search(pattern, page_source, re.IGNORECASE)

            if match:
                country = match.group(1).strip()
                print(f"  🌍 Найдена страна (через regex): {country}")
                return country

            # Альтернативный паттерн: страна происхождения\nСТРАНА
            pattern2 = r'страна происхождения\s*\n\s*(.*?)\s*\n'
            match2 = re.search(pattern2, page_source, re.IGNORECASE)

            if match2:
                country = match2.group(1).strip()
                print(f"  🌍 Найдена страна (через regex2): {country}")
                return country

            return ""

        except Exception as e:
            print(f"  ❌ Ошибка при получении страны: {e}")
            return ""

    def parse_product(self, product: Product) -> Product:
        """Парсит детальную информацию о продукте и заполняет объект Product"""
        print(f"🔍 Парсинг: {product.url}")

        try:
            if not self._safe_get(product.url):
                print(f"❌ Не удалось загрузить страницу: {product.url}")
                return product

            # ОТЛАДКА: сохраняем HTML страницы
            filename = f"debug_{product.url.split('/')[-1]}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"💾 Сохранён HTML: {filename}")

            # 1. Название (из h1)
            product.name = self._get_product_name()

            # 2. Цена
            product.price = self._get_price()

            # 4. Описание продукта
            description = self._get_text(SELECTORS_PDP["product_description"])
            if description:
                description = re.sub(r'\s+', ' ', description).strip()
                product.description = description[:500] if len(description) > 500 else description

            # 5. Инструкция по применению (с раскрытием вкладки!)
            product.instructions = self._get_instructions()

            # 6. Страна-производитель (с раскрытием вкладки!)
            product.country = self._get_country()

            # 3. Рейтинг пользователей (со страницы отзывов!)
            product.rating = self._get_rating_from_review_page(product.url)

            return product

        except Exception as e:
            print(f"❌ Ошибка при парсинге {product.url}: {e}")
            return product

    def load_products_from_csv(self) -> List[Product]:
        """Загружает продукты из CSV файла"""
        products: List[Product] = []

        if not os.path.exists(self.input_path):
            print(f"❌ Файл не найден: {self.input_path}")
            return products

        with open(self.input_path, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                url = row.get("Ссылка на продукт", "") or ""
                url = url.strip()
                if not url:
                    continue

                product = Product(
                    url=url,
                    name=row.get("Наименование", "") or "",
                    price=row.get("Цена", "") or "",
                    rating=row.get("Рейтинг пользователей", "") or "",
                    description=row.get("Описание продукта", "") or "",
                    instructions=row.get("Инструкция по применению", "") or "",
                    country=row.get("Страна-производитель", "") or ""
                )
                products.append(product)

        print(f"📂 Загружено {len(products)} продуктов из {self.input_path}")
        return products

    def save_products_to_csv(self, products: List[Product]) -> None:
        """Сохраняет продукты обратно в CSV файл"""
        with open(self.input_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=Product.CSV_HEADERS)
            writer.writeheader()
            for product in products:
                writer.writerow(product.to_dict())

        print(f"💾 Сохранено {len(products)} продуктов в {self.input_path}")

    def parse_all(self, start_from: int = 0, limit: Optional[int] = None) -> None:
        """Парсит все продукты из CSV файла"""
        products = self.load_products_from_csv()
        total = len(products)

        if total == 0:
            print("⚠️ Нет продуктов для парсинга")
            return

        if start_from >= total:
            print(f"⚠️ start_from={start_from} превышает общее количество продуктов={total}")
            return

        start_idx = start_from
        if limit:
            end_idx = min(start_idx + limit, total)
        else:
            end_idx = total

        print(f"📊 Начинаем парсинг {end_idx - start_idx} продуктов (с {start_idx} по {end_idx - 1} из {total})")

        self.driver = self._init_driver()

        try:
            for i in range(start_idx, end_idx):
                product = products[i]
                print(f"📦 Прогресс: {i + 1}/{total}")

                if not product.url:
                    print(f"⚠️ Продукт {i + 1} не имеет URL, пропускаем")
                    continue

                parsed_product = self.parse_product(product)
                products[i] = parsed_product
                self.save_products_to_csv(products)

        finally:
            if self.driver:
                self.driver.quit()

        print(f"✅ Парсинг завершён! Обработано {end_idx - start_idx} продуктов")

    def parse_missing_only(self) -> None:
        """Парсит только те продукты, у которых отсутствуют данные"""
        products = self.load_products_from_csv()
        missing_indices: List[int] = []

        for i, product in enumerate(products):
            if not product.price and not product.rating and not product.description:
                missing_indices.append(i)

        if not missing_indices:
            print("✅ Нет продуктов с отсутствующими данными")
            return

        print(f"📊 Найдено {len(missing_indices)} продуктов с отсутствующими данными")

        self.driver = self._init_driver()

        try:
            for i in missing_indices:
                print(f"📦 Парсинг пропущенного продукта {i + 1}/{len(products)}")

                if not products[i].url:
                    print(f"⚠️ Продукт {i + 1} не имеет URL, пропускаем")
                    continue

                parsed_product = self.parse_product(products[i])
                products[i] = parsed_product
                self.save_products_to_csv(products)

        finally:
            if self.driver:
                self.driver.quit()
