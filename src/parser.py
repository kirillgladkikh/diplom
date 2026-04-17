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

                # ========== ДОБАВЬТЕ ЭТОТ БЛОК ЗДЕСЬ ==========
                # Ждем загрузки вкладок (после прокруток, чтобы контент точно подгрузился)
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='ga-tabs-tab']"))
                    )
                    print(f"  📑 Вкладки загружены")
                except Exception as e:
                    print(f"  ⚠️ Вкладки не найдены: {e}")
                # ============================================


                # # Прокручиваем страницу для триггера загрузки динамических блоков
                # self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                # time.sleep(1)

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

    def _get_text_by_xpath(self, xpath, default: str = "") -> str:
        """Получает текст элемента по XPath"""
        if isinstance(xpath, list):
            xpath = xpath[0]
        try:
            if self.driver is None:
                return default
            element = self.driver.find_element(By.XPATH, xpath)
            return element.text.strip()
        except NoSuchElementException:
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

    # def _get_rating(self) -> str:
    #     """Получает рейтинг продукта с явным ожиданием загрузки"""
    #     try:
    #         if self.driver is None:
    #             return ""
    #
    #         # Ждём загрузки элемента с рейтингом (увеличиваем до 10 секунд)
    #         wait = WebDriverWait(self.driver, 10)
    #
    #         # Ищем ссылку, которая содержит рейтинг
    #         selectors = [
    #             "a[href*='/review/product/'] ._ga-review-score-point__numeral_y1ia3_15",
    #             "a[href*='/review/product/'] [class*='_ga-review-score-point__numeral']",
    #             "[itemprop='ratingValue']",
    #             "._ga-review-score-point__numeral_y1ia3_15",
    #             "[class*='_ga-review-score-point__numeral']",
    #         ]
    #
    #         for selector in selectors:
    #             try:
    #                 # Ждём появления элемента
    #                 element = wait.until(
    #                     EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    #                 )
    #                 # Ждём, когда текст станет непустым
    #                 wait.until(lambda d: element.text.strip())
    #                 rating = element.text.strip()
    #                 if rating and re.match(r'^\d+(\.\d+)?$', rating):
    #                     print(f"  ✅ Найден рейтинг: {rating}")
    #                     return rating
    #             except TimeoutException:
    #                 continue
    #             except Exception as e:
    #                 print(f"  ⚠️ Ошибка при селекторе {selector}: {e}")
    #                 continue
    #
    #         # Если ничего не нашли, пробуем через XPath
    #         try:
    #             xpath = "//a[contains(@href, '/review/product/')]//div[contains(@class, 'numeral')]"
    #             element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
    #             wait.until(lambda d: element.text.strip())
    #             rating = element.text.strip()
    #             if rating and re.match(r'^\d+(\.\d+)?$', rating):
    #                 print(f"  ✅ Найден рейтинг: {rating} по XPath")
    #                 return rating
    #         except:
    #             pass
    #
    #         return ""
    #
    #     except Exception as e:
    #         print(f"⚠️ Ошибка при получении рейтинга: {e}")
    #         return ""

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

    def _get_country(self) -> str:
        """Получает страну-производитель - комбинированный подход"""
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

            # Получаем весь блок
            container = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class, 'wysiwyg') and contains(text(), 'страна происхождения')]"
            )

            # Способ 1: Через innerHTML и <br>
            inner_html = container.get_attribute('innerHTML')
            import re
            parts = re.split(r'<br\s*/?>', inner_html)

            for i, part in enumerate(parts):
                if 'страна происхождения' in part:
                    if i + 1 < len(parts):
                        country = re.sub(r'<[^>]+>', '', parts[i + 1]).strip()
                        if country:
                            print(f"  🌍 Найдена страна (через <br>): {country}")
                            return country
                    break

            # Способ 2: Если не сработало, пробуем через текст и переносы строк
            full_text = container.text
            lines = full_text.split('\n')
            for i, line in enumerate(lines):
                if 'страна происхождения' in line.lower():
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip():
                            country = lines[j].strip()
                            print(f"  🌍 Найдена страна (через text): {country}")
                            return country
                            break
                    break

        except Exception as e:
            print(f"  ⚠️ Страна не найдена: {e}")

        return ""

    def _extract_country_from_text(self, text: str) -> str:
        """Извлекает страну из текста раздела Дополнительная информация"""
        if not text:
            return ""

        # Ищем строку "страна происхождения" и берём следующую строку
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'страна происхождения' in line.lower():
                # Берём следующую непустую строку
                for j in range(i + 1, min(i + 5, len(lines))):
                    country = lines[j].strip()
                    if country and not country.startswith('изготовитель'):
                        # Очищаем от лишних символов
                        country = re.sub(r'[<>\n\r\t"]', '', country)
                        if country and len(country) < 100:
                            return country
                break

        # Альтернативные паттерны
        patterns = [
            r'страна происхождения[:\s]*([^\n]+)',
            r'страна-производитель[:\s]*([^\n]+)',
            r'страна[:\s]*([^\n]+)',
            r'country of origin[:\s]*([^\n]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                country = match.group(1).strip()
                country = re.sub(r'[<>\n\r\t"]', '', country)
                if country and len(country) < 100:
                    return country

        return ""


    # def _extract_country_from_text(self, text: str) -> str:
    #     """Извлекает страну из текста (из раздела Дополнительная информация)"""
    #     if not text:
    #         return ""
    #
    #     # Ищем строку "страна происхождения" и берём следующую строку
    #     lines = text.split('\n')
    #     for i, line in enumerate(lines):
    #         if 'страна происхождения' in line.lower():
    #             if i + 1 < len(lines):
    #                 country = lines[i + 1].strip()
    #                 country = re.sub(r'[<>\n\r\t]', '', country)
    #                 if country and len(country) < 100:
    #                     return country
    #             break
    #
    #     # Альтернативные паттерны
    #     patterns = [
    #         r'страна происхождения[:\s]*([^\n]+)',
    #         r'страна-производитель[:\s]*([^\n]+)',
    #         r'страна[:\s]*([^\n]+)',
    #         r'изготовитель[:\s]*([^\n]+)',
    #         r'произведено в[:\s]*([^\n]+)',
    #     ]
    #
    #     for pattern in patterns:
    #         match = re.search(pattern, text, re.IGNORECASE)
    #         if match:
    #             country = match.group(1).strip()
    #             country = re.sub(r'[<>\n\r\t]', '', country)
    #             if country and len(country) < 100:
    #                 return country
    #     return ""

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
            price = self._get_text(SELECTORS_PDP["product_price"])
            if price:
                price_clean = re.sub(r'[^\d\s]', '', price).strip()
                if price_clean:
                    product.price = price_clean
                else:
                    product.price = price

            # 4. Описание
            description = self._get_text(SELECTORS_PDP["product_description"])
            if description:
                description = re.sub(r'\s+', ' ', description).strip()
                product.description = description[:500] if len(description) > 500 else description

            # 4. Инструкция
            instructions = self._get_text_by_xpath(SELECTORS_PDP["product_instructions"])
            if instructions:
                product.instructions = re.sub(r'\s+', ' ', instructions).strip()[:300]

            # 5. Страна (с раскрытием вкладки!)
            product.country = self._get_country()

            # 3. Рейтинг (со страницы отзывов) ← ЗДЕСЬ ВЫЗОВ
            product.rating = self._get_rating_from_review_page(product.url)

            # # 3. Рейтинг (с явным ожиданием)
            # product.rating = self._get_rating()
            #
            # # 5. Инструкция по применению
            # instructions = self._get_text_by_xpath(SELECTORS_PDP["product_instructions"])
            # if instructions:
            #     instructions = re.sub(r'\s+', ' ', instructions).strip()
            #     product.instructions = instructions[:300] if len(instructions) > 300 else instructions
            #
            # # 6. Страна-производитель
            # country_block = self._get_text_by_xpath(SELECTORS_PDP["product_country"])
            # if country_block:
            #     product.country = self._extract_country_from_text(country_block)

            rating_display = product.rating if product.rating else "нет"
            print(f"  ✅ {product.name} | {product.price} ₽ | ★ {rating_display}")
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



# """Парсинг детальной информации о товаре"""
#
# import os
# import time
# import random
# import re
# import csv
# from typing import List, Optional
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import NoSuchElementException, TimeoutException
#
# from src.config import (
#     REQUEST_DELAY_MIN, REQUEST_DELAY_MAX, RETRY_COUNT,
#     SELECTORS_PDP, OUTPUT_FILENAME
# )
# from src.product import Product
#
#
# class Parser:
#     """Парсинг детальной информации о продуктах"""
#
#     def __init__(self, input_filename: str = OUTPUT_FILENAME, data_dir: str = "data"):
#         self.input_filename = input_filename
#         self.input_path = os.path.join(data_dir, input_filename)
#         self.driver: Optional[webdriver.Chrome] = None
#
#     def _init_driver(self) -> webdriver.Chrome:
#         """Инициализация драйвера"""
#         chrome_options = Options()
#         chrome_options.add_argument("--headless")
#         chrome_options.add_argument("--no-sandbox")
#         chrome_options.add_argument("--disable-dev-shm-usage")
#         chrome_options.add_argument("--window-size=1920,1080")
#         chrome_options.add_argument("--disable-gpu")
#         chrome_options.add_argument("--disable-logging")
#         chrome_options.add_argument("--log-level=3")
#         chrome_options.set_capability("pageLoadStrategy", "eager")
#
#         driver = webdriver.Chrome(options=chrome_options)
#         driver.set_page_load_timeout(30)
#         return driver
#
#     def _random_delay(self) -> None:
#         """Случайная задержка"""
#         delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
#         time.sleep(delay)
#
#     def restart_driver(self) -> None:
#         """Перезапускает драйвер"""
#         try:
#             if self.driver:
#                 self.driver.quit()
#         except:
#             pass
#         self.driver = self._init_driver()
#
#     def _safe_get(self, url: str, retries: int = RETRY_COUNT) -> bool:
#         """Безопасное получение страницы с повторными попытками"""
#         for attempt in range(retries):
#             try:
#                 if self.driver is None:
#                     self.driver = self._init_driver()
#
#                 self.driver.get(url)
#
#                 # Ждём загрузки body
#                 WebDriverWait(self.driver, 10).until(
#                     EC.presence_of_element_located((By.TAG_NAME, "body"))
#                 )
#
#                 # Дополнительная задержка для динамического контента
#                 self._random_delay()
#
#                 # Прокручиваем страницу для триггера загрузки динамических блоков
#                 self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
#                 time.sleep(0.5)
#
#                 return True
#             except (TimeoutException, Exception) as e:
#                 print(f"⚠️ Попытка {attempt + 1}/{retries} не удалась: {e}")
#                 if attempt == retries - 1:
#                     return False
#                 self._random_delay()
#                 self.restart_driver()
#         return False
#
#     def debug_save_page_source(self, filename: str = "debug_page.html") -> None:
#         """Сохраняет текущий HTML страницы для отладки"""
#         try:
#             if self.driver:
#                 with open(filename, "w", encoding="utf-8") as f:
#                     f.write(self.driver.page_source)
#                 print(f"💾 HTML страницы сохранён в {filename}")
#                 print(f"   Размер файла: {len(self.driver.page_source)} символов")
#         except Exception as e:
#             print(f"⚠️ Ошибка при сохранении HTML: {e}")
#
#     def _get_text(self, selectors, default: str = "") -> str:
#         """Пытается получить текст по одному из CSS селекторов"""
#         if isinstance(selectors, str):
#             selectors = [selectors]
#
#         for selector in selectors:
#             try:
#                 if self.driver is None:
#                     return default
#                 element = self.driver.find_element(By.CSS_SELECTOR, selector)
#                 text = element.text.strip()
#                 if text:
#                     return text
#             except NoSuchElementException:
#                 continue
#         return default
#
#     def _get_text_by_xpath(self, xpath, default: str = "") -> str:
#         """Получает текст элемента по XPath"""
#         if isinstance(xpath, list):
#             xpath = xpath[0]
#         try:
#             if self.driver is None:
#                 return default
#             element = self.driver.find_element(By.XPATH, xpath)
#             return element.text.strip()
#         except NoSuchElementException:
#             return default
#
#     def _get_product_name(self) -> str:
#         """Получает название продукта из h1"""
#         try:
#             if self.driver is None:
#                 return ""
#             h1 = self.driver.find_element(By.CSS_SELECTOR, "h1")
#             return h1.text.strip()
#         except Exception as e:
#             print(f"⚠️ Не удалось получить название: {e}")
#             return ""
#
#     def _get_rating(self) -> str:
#         """Получает рейтинг продукта с явным ожиданием загрузки"""
#         try:
#             if self.driver is None:
#                 return ""
#
#             # Ждём загрузки элемента с рейтингом (максимум 5 секунд)
#             wait = WebDriverWait(self.driver, 5)
#
#             # Пробуем разные селекторы
#             selectors = [
#                 "[itemprop='ratingValue']",
#                 "._ga-review-score-point__numeral_y1ia3_15",
#                 "[class*='_ga-review-score-point__numeral']",
#                 "[class*='rating-value']",
#             ]
#
#             for selector in selectors:
#                 try:
#                     # Ждём появления элемента
#                     element = wait.until(
#                         EC.presence_of_element_located((By.CSS_SELECTOR, selector))
#                     )
#                     rating = element.text.strip()
#                     if rating and re.match(r'^\d+(\.\d+)?$', rating):
#                         return rating
#                 except:
#                     continue
#
#             return ""
#
#         except Exception as e:
#             print(f"⚠️ Ошибка при получении рейтинга: {e}")
#             return ""
#
#     def _extract_country_from_text(self, text: str) -> str:
#         """Извлекает страну из текста (из раздела Дополнительная информация)"""
#         if not text:
#             return ""
#
#         # Ищем строку "страна происхождения" и берём следующую строку
#         lines = text.split('\n')
#         for i, line in enumerate(lines):
#             if 'страна происхождения' in line.lower():
#                 if i + 1 < len(lines):
#                     country = lines[i + 1].strip()
#                     country = re.sub(r'[<>\n\r\t]', '', country)
#                     if country and len(country) < 100:
#                         return country
#                 break
#
#         # Альтернативные паттерны
#         patterns = [
#             r'страна происхождения[:\s]*([^\n]+)',
#             r'страна-производитель[:\s]*([^\n]+)',
#             r'страна[:\s]*([^\n]+)',
#             r'изготовитель[:\s]*([^\n]+)',
#             r'произведено в[:\s]*([^\n]+)',
#         ]
#
#         for pattern in patterns:
#             match = re.search(pattern, text, re.IGNORECASE)
#             if match:
#                 country = match.group(1).strip()
#                 country = re.sub(r'[<>\n\r\t]', '', country)
#                 if country and len(country) < 100:
#                     return country
#         return ""
#
#     def parse_product(self, product: Product) -> Product:
#         """Парсит детальную информацию о продукте и заполняет объект Product"""
#         print(f"🔍 Парсинг: {product.url}")
#
#         try:
#             if not self._safe_get(product.url):
#                 print(f"❌ Не удалось загрузить страницу: {product.url}")
#                 return product
#
#             # ОТЛАДКА: сохраняем HTML страницы
#             filename = f"debug_{product.url.split('/')[-1]}.html"
#             with open(filename, "w", encoding="utf-8") as f:
#                 f.write(self.driver.page_source)
#             print(f"💾 Сохранён HTML: {filename}")
#             # self.debug_save_page_source(f"debug_{product.url.split('/')[-1]}.html")
#
#             # 1. Название (из h1)
#             product.name = self._get_product_name()
#
#             # 2. Цена
#             price = self._get_text(SELECTORS_PDP["product_price"])
#             if price:
#                 price_clean = re.sub(r'[^\d\s]', '', price).strip()
#                 if price_clean:
#                     product.price = price_clean
#                 else:
#                     product.price = price
#
#             # 3. Рейтинг (с явным ожиданием)
#             product.rating = self._get_rating()
#
#             # 4. Описание
#             description = self._get_text(SELECTORS_PDP["product_description"])
#             if description:
#                 description = re.sub(r'\s+', ' ', description).strip()
#                 product.description = description[:500] if len(description) > 500 else description
#
#             # 5. Инструкция по применению
#             instructions = self._get_text_by_xpath(SELECTORS_PDP["product_instructions"])
#             if instructions:
#                 instructions = re.sub(r'\s+', ' ', instructions).strip()
#                 product.instructions = instructions[:300] if len(instructions) > 300 else instructions
#
#             # 6. Страна-производитель
#             country_block = self._get_text_by_xpath(SELECTORS_PDP["product_country"])
#             if country_block:
#                 product.country = self._extract_country_from_text(country_block)
#
#             rating_display = product.rating if product.rating else "нет"
#             print(f"  ✅ {product.name} | {product.price} ₽ | ★ {rating_display}")
#             return product
#
#         except Exception as e:
#             print(f"❌ Ошибка при парсинге {product.url}: {e}")
#             return product
#
#     def load_products_from_csv(self) -> List[Product]:
#         """Загружает продукты из CSV файла"""
#         products: List[Product] = []
#
#         if not os.path.exists(self.input_path):
#             print(f"❌ Файл не найден: {self.input_path}")
#             return products
#
#         with open(self.input_path, 'r', encoding='utf-8-sig') as csvfile:
#             reader = csv.DictReader(csvfile)
#             for row in reader:
#                 url = row.get("Ссылка на продукт", "") or ""
#                 url = url.strip()
#                 if not url:
#                     continue
#
#                 product = Product(
#                     url=url,
#                     name=row.get("Наименование", "") or "",
#                     price=row.get("Цена", "") or "",
#                     rating=row.get("Рейтинг пользователей", "") or "",
#                     description=row.get("Описание продукта", "") or "",
#                     instructions=row.get("Инструкция по применению", "") or "",
#                     country=row.get("Страна-производитель", "") or ""
#                 )
#                 products.append(product)
#
#         print(f"📂 Загружено {len(products)} продуктов из {self.input_path}")
#         return products
#
#     def save_products_to_csv(self, products: List[Product]) -> None:
#         """Сохраняет продукты обратно в CSV файл"""
#         with open(self.input_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
#             writer = csv.DictWriter(csvfile, fieldnames=Product.CSV_HEADERS)
#             writer.writeheader()
#             for product in products:
#                 writer.writerow(product.to_dict())
#
#         print(f"💾 Сохранено {len(products)} продуктов в {self.input_path}")
#
#     def parse_all(self, start_from: int = 0, limit: Optional[int] = None) -> None:
#         """Парсит все продукты из CSV файла"""
#         products = self.load_products_from_csv()
#         total = len(products)
#
#         if total == 0:
#             print("⚠️ Нет продуктов для парсинга")
#             return
#
#         if start_from >= total:
#             print(f"⚠️ start_from={start_from} превышает общее количество продуктов={total}")
#             return
#
#         start_idx = start_from
#         if limit:
#             end_idx = min(start_idx + limit, total)
#         else:
#             end_idx = total
#
#         print(f"📊 Начинаем парсинг {end_idx - start_idx} продуктов (с {start_idx} по {end_idx - 1} из {total})")
#
#         self.driver = self._init_driver()
#
#         try:
#             for i in range(start_idx, end_idx):
#                 product = products[i]
#                 print(f"📦 Прогресс: {i + 1}/{total}")
#
#                 if not product.url:
#                     print(f"⚠️ Продукт {i + 1} не имеет URL, пропускаем")
#                     continue
#
#                 parsed_product = self.parse_product(product)
#                 products[i] = parsed_product
#                 self.save_products_to_csv(products)
#
#         finally:
#             if self.driver:
#                 self.driver.quit()
#
#         print(f"✅ Парсинг завершён! Обработано {end_idx - start_idx} продуктов")
#
#     def parse_missing_only(self) -> None:
#         """Парсит только те продукты, у которых отсутствуют данные"""
#         products = self.load_products_from_csv()
#         missing_indices: List[int] = []
#
#         for i, product in enumerate(products):
#             if not product.price and not product.rating and not product.description:
#                 missing_indices.append(i)
#
#         if not missing_indices:
#             print("✅ Нет продуктов с отсутствующими данными")
#             return
#
#         print(f"📊 Найдено {len(missing_indices)} продуктов с отсутствующими данными")
#
#         self.driver = self._init_driver()
#
#         try:
#             for i in missing_indices:
#                 print(f"📦 Парсинг пропущенного продукта {i + 1}/{len(products)}")
#
#                 if not products[i].url:
#                     print(f"⚠️ Продукт {i + 1} не имеет URL, пропускаем")
#                     continue
#
#                 parsed_product = self.parse_product(products[i])
#                 products[i] = parsed_product
#                 self.save_products_to_csv(products)
#
#         finally:
#             if self.driver:
#                 self.driver.quit()
#
#
#
#
# # """Парсинг детальной информации о товаре"""
# #
# # import os
# # import time
# # import random
# # import re
# # import csv
# # from typing import List, Optional
# # from selenium import webdriver
# # from selenium.webdriver.chrome.options import Options
# # from selenium.webdriver.common.by import By
# # from selenium.common.exceptions import NoSuchElementException, TimeoutException
# #
# # from src.config import (
# #     REQUEST_DELAY_MIN, REQUEST_DELAY_MAX, RETRY_COUNT,
# #     SELECTORS_PDP, OUTPUT_FILENAME
# # )
# # from src.product import Product
# #
# #
# # class Parser:
# #     """Парсинг детальной информации о продуктах"""
# #
# #     def __init__(self, input_filename: str = OUTPUT_FILENAME, data_dir: str = "data"):
# #         self.input_filename = input_filename
# #         self.input_path = os.path.join(data_dir, input_filename)
# #         self.driver: Optional[webdriver.Chrome] = None
# #
# #     def _init_driver(self) -> webdriver.Chrome:
# #         """Инициализация драйвера"""
# #         chrome_options = Options()
# #         chrome_options.add_argument("--headless")
# #         chrome_options.add_argument("--no-sandbox")
# #         chrome_options.add_argument("--disable-dev-shm-usage")
# #         chrome_options.add_argument("--window-size=1920,1080")
# #         chrome_options.add_argument("--disable-gpu")
# #         chrome_options.add_argument("--disable-logging")
# #         chrome_options.add_argument("--log-level=3")
# #         chrome_options.set_capability("pageLoadStrategy", "eager")
# #
# #         driver = webdriver.Chrome(options=chrome_options)
# #         driver.set_page_load_timeout(30)
# #         return driver
# #
# #     def _random_delay(self) -> None:
# #         """Случайная задержка"""
# #         delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
# #         time.sleep(delay)
# #
# #     def _safe_get(self, url: str, retries: int = RETRY_COUNT) -> bool:
# #         """Безопасное получение страницы с повторными попытками"""
# #         for attempt in range(retries):
# #             try:
# #                 if self.driver is None:
# #                     self.driver = self._init_driver()
# #                 self.driver.get(url)
# #                 self._random_delay()
# #                 return True
# #             except (TimeoutException, Exception) as e:
# #                 print(f"⚠️ Попытка {attempt + 1}/{retries} не удалась: {e}")
# #                 if attempt == retries - 1:
# #                     return False
# #                 self._random_delay()
# #         return False
# #
# #     def _get_text(self, selectors, default: str = "") -> str:
# #         """Пытается получить текст по одному из CSS селекторов"""
# #         if isinstance(selectors, str):
# #             selectors = [selectors]
# #
# #         for selector in selectors:
# #             try:
# #                 if self.driver is None:
# #                     return default
# #                 element = self.driver.find_element(By.CSS_SELECTOR, selector)
# #                 text = element.text.strip()
# #                 if text:
# #                     return text
# #             except NoSuchElementException:
# #                 continue
# #         return default
# #
# #     def _get_text_by_xpath(self, xpath, default: str = "") -> str:
# #         """Получает текст элемента по XPath"""
# #         if isinstance(xpath, list):
# #             xpath = xpath[0]
# #         try:
# #             if self.driver is None:
# #                 return default
# #             element = self.driver.find_element(By.XPATH, xpath)
# #             return element.text.strip()
# #         except NoSuchElementException:
# #             return default
# #
# #     def _get_product_name(self) -> str:
# #         """Получает название продукта из h1"""
# #         try:
# #             if self.driver is None:
# #                 return ""
# #             h1 = self.driver.find_element(By.CSS_SELECTOR, "h1")
# #             return h1.text.strip()
# #         except Exception as e:
# #             print(f"⚠️ Не удалось получить название: {e}")
# #             return ""
# #
# #     def _get_rating(self) -> str:
# #         """Получает рейтинг продукта (оценка товара)"""
# #         try:
# #             if self.driver is None:
# #                 return ""
# #
# #             # Вариант 1: Ищем по itemprop='ratingValue'
# #             try:
# #                 rating_element = self.driver.find_element(By.CSS_SELECTOR, "[itemprop='ratingValue']")
# #                 rating = rating_element.text.strip()
# #                 if rating:
# #                     return rating
# #             except:
# #                 pass
# #
# #             # Вариант 2: Ищем по части класса (более надёжно)
# #             selectors = [
# #                 "[class*='_ga-review-score-point__numeral']",
# #                 "[class*='rating-value']",
# #             ]
# #
# #             for selector in selectors:
# #                 try:
# #                     elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
# #                     for element in elements:
# #                         text = element.text.strip()
# #                         # Проверяем, что текст похож на число с плавающей точкой
# #                         if text and re.match(r'^\d+(\.\d+)?$', text):
# #                             return text
# #                 except:
# #                     continue
# #
# #             # Вариант 3: Ищем по XPath (самый надёжный, но медленный)
# #             try:
# #                 xpath = "//div[contains(@class, '_ga-review-score-point__numeral')]"
# #                 element = self.driver.find_element(By.XPATH, xpath)
# #                 rating = element.text.strip()
# #                 if rating and re.match(r'^\d+(\.\d+)?$', rating):
# #                     return rating
# #             except:
# #                 pass
# #
# #             return ""
# #
# #         except Exception as e:
# #             print(f"⚠️ Ошибка при получении рейтинга: {e}")
# #             return ""
# #
# #     # def _get_rating(self) -> str:
# #     #     """Получает рейтинг продукта"""
# #     #     rating = self._get_text(SELECTORS_PDP["product_rating"])
# #     #     if rating:
# #     #         # Очищаем рейтинг, оставляем только цифры и точку
# #     #         rating_clean = re.sub(r'[^\d.]', '', rating).strip()
# #     #         if rating_clean:
# #     #             return rating_clean
# #     #         return rating
# #     #     return ""
# #
# #     def _extract_country_from_text(self, text: str) -> str:
# #         """Извлекает страну из текста (например, из раздела Дополнительная информация)"""
# #         if not text:
# #             return ""
# #
# #         # Ищем строку "страна происхождения" и берём следующую строку
# #         lines = text.split('\n')
# #         for i, line in enumerate(lines):
# #             if 'страна происхождения' in line.lower():
# #                 if i + 1 < len(lines):
# #                     country = lines[i + 1].strip()
# #                     if country and len(country) < 100:
# #                         return country
# #                 break
# #
# #         # Альтернативные паттерны
# #         patterns = [
# #             r'страна происхождения[:\s]*([^\n]+)',
# #             r'страна-производитель[:\s]*([^\n]+)',
# #             r'страна[:\s]*([^\n]+)',
# #         ]
# #
# #         for pattern in patterns:
# #             match = re.search(pattern, text, re.IGNORECASE)
# #             if match:
# #                 country = match.group(1).strip()
# #                 country = re.sub(r'[<>\n\r\t]', '', country)
# #                 if country and len(country) < 100:
# #                     return country
# #         return ""
# #
# #     def debug_page_source(self):
# #         """Сохраняет HTML страницы для отладки"""
# #         if self.driver:
# #             with open("debug_page.html", "w", encoding="utf-8") as f:
# #                 f.write(self.driver.page_source)
# #             print("💾 HTML страницы сохранён в debug_page.html")
# #
# #     def parse_product(self, product: Product) -> Product:
# #         """Парсит детальную информацию о продукте и заполняет объект Product"""
# #         print(f"🔍 Парсинг: {product.url}")
# #
# #         try:
# #             if not self._safe_get(product.url):
# #                 print(f"❌ Не удалось загрузить страницу: {product.url}")
# #                 return product
# #
# #             # Принудительно ждём загрузку рейтинга (если он есть)
# #             time.sleep(3)  # Дополнительная задержка
# #
# #             # Прокручиваем страницу вниз, чтобы загрузить динамический контент
# #             self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
# #             time.sleep(3)
# #
# #             # 1. Название (из h1)
# #             product.name = self._get_product_name()
# #
# #             # 2. Цена
# #             price = self._get_text(SELECTORS_PDP["product_price"])
# #             if price:
# #                 price = re.sub(r'[^\d\s]', '', price).strip()
# #                 product.price = price
# #
# #             # Для отладки
# #             self.debug_page_source()
# #
# #             # 3. Рейтинг
# #             product.rating = self._get_rating()
# #             # rating = self._get_text(SELECTORS_PDP["product_rating"])
# #             # if rating:
# #             #     product.rating = rating
# #
# #             # 4. Описание
# #             description = self._get_text(SELECTORS_PDP["product_description"])
# #             if description:
# #                 description = re.sub(r'\s+', ' ', description).strip()
# #                 product.description = description[:500] if len(description) > 500 else description
# #
# #             # 5. Инструкция по применению
# #             instructions = self._get_text_by_xpath(SELECTORS_PDP["product_instructions"])
# #             if instructions:
# #                 instructions = re.sub(r'\s+', ' ', instructions).strip()
# #                 product.instructions = instructions[:300] if len(instructions) > 300 else instructions
# #
# #             # 6. Страна-производитель (из раздела Дополнительная информация)
# #             country_block = self._get_text_by_xpath(SELECTORS_PDP["product_country"])
# #             if country_block:
# #                 product.country = self._extract_country_from_text(country_block)
# #             else:
# #                 # Если не нашли, пробуем из описания
# #                 product.country = self._extract_country_from_text(description)
# #
# #             rating_display = product.rating if product.rating else "нет"
# #             print(f"  ✅ {product.name} | {product.price} ₽ | ★ {rating_display}")
# #             # print(f"  ✅ {product.name} | {product.price} ₽ | ★ {product.rating}")
# #
# #             return product
# #
# #         except Exception as e:
# #             print(f"❌ Ошибка при парсинге {product.url}: {e}")
# #             return product
# #
# #     def load_products_from_csv(self) -> List[Product]:
# #         """Загружает продукты из CSV файла"""
# #         products: List[Product] = []
# #
# #         if not os.path.exists(self.input_path):
# #             print(f"❌ Файл не найден: {self.input_path}")
# #             return products
# #
# #         with open(self.input_path, 'r', encoding='utf-8-sig') as csvfile:
# #             reader = csv.DictReader(csvfile)
# #             for row in reader:
# #                 url = row.get("Ссылка на продукт", "") or ""
# #                 url = url.strip()
# #                 if not url:
# #                     continue
# #
# #                 product = Product(
# #                     url=url,
# #                     name=row.get("Наименование", "") or "",
# #                     price=row.get("Цена", "") or "",
# #                     rating=row.get("Рейтинг пользователей", "") or "",
# #                     description=row.get("Описание продукта", "") or "",
# #                     instructions=row.get("Инструкция по применению", "") or "",
# #                     country=row.get("Страна-производитель", "") or ""
# #                 )
# #                 products.append(product)
# #
# #         print(f"📂 Загружено {len(products)} продуктов из {self.input_path}")
# #         return products
# #
# #     def save_products_to_csv(self, products: List[Product]) -> None:
# #         """Сохраняет продукты обратно в CSV файл"""
# #         with open(self.input_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
# #             writer = csv.DictWriter(csvfile, fieldnames=Product.CSV_HEADERS)
# #             writer.writeheader()
# #             for product in products:
# #                 writer.writerow(product.to_dict())
# #
# #         print(f"💾 Сохранено {len(products)} продуктов в {self.input_path}")
# #
# #     def parse_all(self, start_from: int = 0, limit: Optional[int] = None) -> None:
# #         """Парсит все продукты из CSV файла"""
# #         products = self.load_products_from_csv()
# #         total = len(products)
# #
# #         if total == 0:
# #             print("⚠️ Нет продуктов для парсинга")
# #             return
# #
# #         if start_from >= total:
# #             print(f"⚠️ start_from={start_from} превышает общее количество продуктов={total}")
# #             return
# #
# #         start_idx = start_from
# #         if limit:
# #             end_idx = min(start_idx + limit, total)
# #         else:
# #             end_idx = total
# #
# #         print(f"📊 Начинаем парсинг {end_idx - start_idx} продуктов (с {start_idx} по {end_idx - 1} из {total})")
# #
# #         self.driver = self._init_driver()
# #
# #         try:
# #             for i in range(start_idx, end_idx):
# #                 product = products[i]
# #                 print(f"📦 Прогресс: {i + 1}/{total}")
# #
# #                 if not product.url:
# #                     print(f"⚠️ Продукт {i + 1} не имеет URL, пропускаем")
# #                     continue
# #
# #                 parsed_product = self.parse_product(product)
# #                 products[i] = parsed_product
# #                 self.save_products_to_csv(products)
# #
# #         finally:
# #             if self.driver:
# #                 self.driver.quit()
# #
# #         print(f"✅ Парсинг завершён! Обработано {end_idx - start_idx} продуктов")
# #
# #     def parse_missing_only(self) -> None:
# #         """Парсит только те продукты, у которых отсутствуют данные"""
# #         products = self.load_products_from_csv()
# #         missing_indices: List[int] = []
# #
# #         for i, product in enumerate(products):
# #             if not product.price and not product.rating and not product.description:
# #                 missing_indices.append(i)
# #
# #         if not missing_indices:
# #             print("✅ Нет продуктов с отсутствующими данными")
# #             return
# #
# #         print(f"📊 Найдено {len(missing_indices)} продуктов с отсутствующими данными")
# #
# #         self.driver = self._init_driver()
# #
# #         try:
# #             for i in missing_indices:
# #                 print(f"📦 Парсинг пропущенного продукта {i + 1}/{len(products)}")
# #
# #                 if not products[i].url:
# #                     print(f"⚠️ Продукт {i + 1} не имеет URL, пропускаем")
# #                     continue
# #
# #                 parsed_product = self.parse_product(products[i])
# #                 products[i] = parsed_product
# #                 self.save_products_to_csv(products)
# #
# #         finally:
# #             if self.driver:
# #                 self.driver.quit()
# #
# #
# #
# #
# # # """Парсинг детальной информации о товаре"""
# # #
# # # import os
# # # import time
# # # import random
# # # import re
# # # import csv
# # # from typing import List, Optional, Dict
# # # from selenium import webdriver
# # # from selenium.webdriver.chrome.options import Options
# # # from selenium.webdriver.common.by import By
# # # from selenium.common.exceptions import NoSuchElementException, TimeoutException
# # #
# # # from src.config import (
# # #     REQUEST_DELAY_MIN, REQUEST_DELAY_MAX, RETRY_COUNT,
# # #     SELECTORS_PDP, OUTPUT_FILENAME
# # # )
# # # from src.product import Product
# # #
# # #
# # # class Parser:
# # #     """Парсинг детальной информации о продуктах"""
# # #
# # #     def __init__(self, input_filename: str = OUTPUT_FILENAME, data_dir: str = "data"):
# # #         self.input_filename = input_filename
# # #         self.input_path = os.path.join(data_dir, input_filename)
# # #         self.driver: Optional[webdriver.Chrome] = None
# # #
# # #     def _init_driver(self) -> webdriver.Chrome:
# # #         """Инициализация драйвера"""
# # #         chrome_options = Options()
# # #         chrome_options.add_argument("--headless")
# # #         chrome_options.add_argument("--no-sandbox")
# # #         chrome_options.add_argument("--disable-dev-shm-usage")
# # #         chrome_options.add_argument("--window-size=1920,1080")
# # #         chrome_options.add_argument("--disable-gpu")
# # #         chrome_options.add_argument("--disable-logging")
# # #         chrome_options.add_argument("--log-level=3")
# # #         chrome_options.set_capability("pageLoadStrategy", "eager")
# # #
# # #         driver = webdriver.Chrome(options=chrome_options)
# # #         driver.set_page_load_timeout(30)
# # #         return driver
# # #
# # #     def _random_delay(self) -> None:
# # #         """Случайная задержка"""
# # #         delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
# # #         time.sleep(delay)
# # #
# # #     def _safe_get(self, url: str, retries: int = RETRY_COUNT) -> bool:
# # #         """Безопасное получение страницы с повторными попытками"""
# # #         for attempt in range(retries):
# # #             try:
# # #                 if self.driver is None:
# # #                     self.driver = self._init_driver()
# # #                 self.driver.get(url)
# # #                 self._random_delay()
# # #                 return True
# # #             except (TimeoutException, Exception) as e:
# # #                 print(f"⚠️ Попытка {attempt + 1}/{retries} не удалась: {e}")
# # #                 if attempt == retries - 1:
# # #                     return False
# # #                 self._random_delay()
# # #         return False
# # #
# # #     def _get_text(self, selectors, default: str = "") -> str:
# # #         """Пытается получить текст по одному из CSS селекторов"""
# # #         if isinstance(selectors, str):
# # #             selectors = [selectors]
# # #
# # #         for selector in selectors:
# # #             try:
# # #                 if self.driver is None:
# # #                     return default
# # #                 element = self.driver.find_element(By.CSS_SELECTOR, selector)
# # #                 text = element.text.strip()
# # #                 if text:
# # #                     return text
# # #             except NoSuchElementException:
# # #                 continue
# # #         return default
# # #
# # #     def _get_text_by_xpath(self, xpath, default: str = "") -> str:
# # #         """Получает текст элемента по XPath"""
# # #         if isinstance(xpath, list):
# # #             xpath = xpath[0]
# # #         try:
# # #             if self.driver is None:
# # #                 return default
# # #             element = self.driver.find_element(By.XPATH, xpath)
# # #             return element.text.strip()
# # #         except NoSuchElementException:
# # #             return default
# # #
# # #     def _get_product_name(self) -> str:
# # #         """Получает название продукта из h1"""
# # #         try:
# # #             if self.driver is None:
# # #                 return ""
# # #             h1 = self.driver.find_element(By.CSS_SELECTOR, "h1")
# # #             return h1.text.strip()
# # #         except Exception as e:
# # #             print(f"⚠️ Не удалось получить название: {e}")
# # #             return ""
# # #
# # #     def _get_country_from_description(self, description_text: str) -> str:
# # #         """Извлекает страну из описания"""
# # #         if not description_text:
# # #             return ""
# # #
# # #         patterns = [
# # #             r'страна происхождения[:\s]*([^\n]+)',
# # #             r'страна-производитель[:\s]*([^\n]+)',
# # #             r'страна[:\s]*([^\n]+)',
# # #             r'изготовитель[:\s]*([^\n]+)',
# # #             r'произведено в[:\s]*([^\n]+)',
# # #         ]
# # #
# # #         for pattern in patterns:
# # #             match = re.search(pattern, description_text, re.IGNORECASE)
# # #             if match:
# # #                 country = match.group(1).strip()
# # #                 country = re.sub(r'[<>\n\r\t]', '', country)
# # #                 if country and len(country) < 100:
# # #                     return country
# # #         return ""
# # #
# # #     def parse_product(self, product: Product) -> Product:
# # #         """Парсит детальную информацию о продукте и заполняет объект Product"""
# # #         print(f"🔍 Парсинг: {product.url}")
# # #
# # #         try:
# # #             if not self._safe_get(product.url):
# # #                 print(f"❌ Не удалось загрузить страницу: {product.url}")
# # #                 return product
# # #
# # #             # 1. Название (из h1)
# # #             product.name = self._get_product_name()
# # #
# # #             # 2. Цена
# # #             price = self._get_text(SELECTORS_PDP["product_price"])
# # #             if price:
# # #                 price = re.sub(r'[^\d\s]', '', price).strip()
# # #                 product.price = price
# # #
# # #             # 3. Рейтинг
# # #             rating = self._get_text(SELECTORS_PDP["product_rating"])
# # #             if rating:
# # #                 product.rating = rating
# # #
# # #             # 4. Описание
# # #             description = self._get_text(SELECTORS_PDP["product_description"])
# # #             if description:
# # #                 description = re.sub(r'\s+', ' ', description).strip()
# # #                 product.description = description[:500] if len(description) > 500 else description
# # #
# # #             # 5. Инструкция по применению (XPath)
# # #             instructions = self._get_text_by_xpath(SELECTORS_PDP["product_instructions"])
# # #             if instructions:
# # #                 instructions = re.sub(r'\s+', ' ', instructions).strip()
# # #                 product.instructions = instructions[:300] if len(instructions) > 300 else instructions
# # #
# # #             # 6. Страна-производитель (XPath)
# # #             country = self._get_text_by_xpath(SELECTORS_PDP["product_country"])
# # #             if country:
# # #                 product.country = country.strip()
# # #             else:
# # #                 product.country = self._get_country_from_description(description)
# # #
# # #             print(f"  ✅ {product.name} | {product.price} ₽ | ★ {product.rating}")
# # #             return product
# # #
# # #         except Exception as e:
# # #             print(f"❌ Ошибка при парсинге {product.url}: {e}")
# # #             return product
# # #
# # #     def load_products_from_csv(self) -> List[Product]:
# # #         """Загружает продукты из CSV файла"""
# # #         products: List[Product] = []
# # #
# # #         if not os.path.exists(self.input_path):
# # #             print(f"❌ Файл не найден: {self.input_path}")
# # #             return products
# # #
# # #         with open(self.input_path, 'r', encoding='utf-8-sig') as csvfile:
# # #             reader = csv.DictReader(csvfile)
# # #             for row_dict in reader:
# # #                 # Используем явное преобразование через dict
# # #                 row: Dict[str, str] = dict(row_dict)
# # #
# # #                 url = row.get("Ссылка на продукт", "") or ""
# # #                 url = url.strip()
# # #                 # Пропускаем пустые строки
# # #                 if not url:
# # #                     continue
# # #
# # #                 product = Product(
# # #                     url=url,
# # #                     name=row.get("Наименование", "") or "",
# # #                     price=row.get("Цена", "") or "",
# # #                     rating=row.get("Рейтинг пользователей", "") or "",
# # #                     description=row.get("Описание продукта", "") or "",
# # #                     instructions=row.get("Инструкция по применению", "") or "",
# # #                     country=row.get("Страна-производитель", "") or ""
# # #                 )
# # #                 products.append(product)
# # #
# # #         print(f"📂 Загружено {len(products)} продуктов из {self.input_path}")
# # #         return products
# # #
# # #     def save_products_to_csv(self, products: List[Product]) -> None:
# # #         """Сохраняет продукты обратно в CSV файл"""
# # #         with open(self.input_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
# # #             writer = csv.DictWriter(csvfile, fieldnames=Product.CSV_HEADERS)
# # #             writer.writeheader()
# # #             for product in products:
# # #                 writer.writerow(product.to_dict())
# # #
# # #         print(f"💾 Сохранено {len(products)} продуктов в {self.input_path}")
# # #
# # #     def parse_all(self, start_from: int = 0, limit: Optional[int] = None) -> None:
# # #         """Парсит все продукты из CSV файла"""
# # #         products = self.load_products_from_csv()
# # #         total = len(products)
# # #
# # #         if total == 0:
# # #             print("⚠️ Нет продуктов для парсинга")
# # #             return
# # #
# # #         # Проверяем, что start_from не выходит за пределы
# # #         if start_from >= total:
# # #             print(f"⚠️ start_from={start_from} превышает общее количество продуктов={total}")
# # #             return
# # #
# # #         # Определяем диапазон парсинга
# # #         start_idx = start_from
# # #         if limit:
# # #             end_idx = min(start_idx + limit, total)
# # #         else:
# # #             end_idx = total
# # #
# # #         print(f"📊 Начинаем парсинг {end_idx - start_idx} продуктов (с {start_idx} по {end_idx - 1} из {total})")
# # #
# # #         self.driver = self._init_driver()
# # #
# # #         try:
# # #             for i in range(start_idx, end_idx):
# # #                 product = products[i]
# # #                 print(f"📦 Прогресс: {i + 1}/{total}")
# # #
# # #                 # Проверяем, что URL не пустой
# # #                 if not product.url:
# # #                     print(f"⚠️ Продукт {i + 1} не имеет URL, пропускаем")
# # #                     continue
# # #
# # #                 parsed_product = self.parse_product(product)
# # #                 products[i] = parsed_product
# # #
# # #                 # Сохраняем после каждого продукта (на случай прерывания)
# # #                 self.save_products_to_csv(products)
# # #
# # #         finally:
# # #             if self.driver:
# # #                 self.driver.quit()
# # #
# # #         print(f"✅ Парсинг завершён! Обработано {end_idx - start_idx} продуктов")
# # #
# # #     def parse_missing_only(self) -> None:
# # #         """Парсит только те продукты, у которых отсутствуют данные"""
# # #         products = self.load_products_from_csv()
# # #         missing_indices: List[int] = []
# # #
# # #         for i, product in enumerate(products):
# # #             if not product.price and not product.rating and not product.description:
# # #                 missing_indices.append(i)
# # #
# # #         if not missing_indices:
# # #             print("✅ Нет продуктов с отсутствующими данными")
# # #             return
# # #
# # #         print(f"📊 Найдено {len(missing_indices)} продуктов с отсутствующими данными")
# # #
# # #         self.driver = self._init_driver()
# # #
# # #         try:
# # #             for i in missing_indices:
# # #                 print(f"📦 Парсинг пропущенного продукта {i + 1}/{len(products)}")
# # #
# # #                 if not products[i].url:
# # #                     print(f"⚠️ Продукт {i + 1} не имеет URL, пропускаем")
# # #                     continue
# # #
# # #                 parsed_product = self.parse_product(products[i])
# # #                 products[i] = parsed_product
# # #                 self.save_products_to_csv(products)
# # #
# # #         finally:
# # #             if self.driver:
# # #                 self.driver.quit()
# # #
# # #
# # #
# # #
# # # # import csv
# # # # import time
# # # # import re
# # # # import random
# # # # from selenium import webdriver
# # # # from selenium.webdriver.chrome.options import Options
# # # # from selenium.webdriver.common.by import By
# # # # from selenium.common.exceptions import WebDriverException, TimeoutException
# # # # import logging
# # # #
# # # # # Настройка логирования
# # # # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# # # # logger = logging.getLogger(__name__)
# # # #
# # # #
# # # # class Parser:
# # # #     def __init__(self, base_url, test_mode=True):
# # # #         self.base_url = base_url
# # # #         self.test_mode = test_mode
# # # #         self.product_links = set()
# # # #         self.driver = None
# # # #
# # # #         if self.test_mode:
# # # #             logger.info("🔧 РЕЖИМ ТЕСТИРОВАНИЯ: будет обработано только 3 страницы")
# # # #
# # # #     def init_driver(self):
# # # #         """Инициализация драйвера с улучшенными настройками"""
# # # #         chrome_options = Options()
# # # #         chrome_options.add_argument("--headless")
# # # #         chrome_options.add_argument("--no-sandbox")
# # # #         chrome_options.add_argument("--disable-dev-shm-usage")
# # # #         chrome_options.add_argument("--window-size=1920,1080")
# # # #         chrome_options.add_argument("--disable-gpu")
# # # #         chrome_options.add_argument("--disable-extensions")
# # # #         chrome_options.add_argument("--disable-logging")
# # # #         chrome_options.add_argument("--log-level=3")
# # # #         chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
# # # #
# # # #         chrome_options.set_capability("pageLoadStrategy", "eager")
# # # #
# # # #         driver = webdriver.Chrome(options=chrome_options)
# # # #         driver.set_page_load_timeout(30)
# # # #         driver.implicitly_wait(10)
# # # #
# # # #         return driver
# # # #
# # # #     def random_delay(self, min_seconds=0.3, max_seconds=1.5):
# # # #         """Случайная задержка для имитации человеческого поведения"""
# # # #         delay = random.uniform(min_seconds, max_seconds)
# # # #         time.sleep(delay)
# # # #
# # # #     def safe_get(self, url, retries=3):
# # # #         """Безопасное получение страницы с повторными попытками"""
# # # #         for attempt in range(retries):
# # # #             try:
# # # #                 if self.driver is None:
# # # #                     self.driver = self.init_driver()
# # # #                 self.driver.get(url)
# # # #                 self.random_delay(0.5, 1.5)  # Случайная задержка после загрузки
# # # #                 return True
# # # #             except (WebDriverException, TimeoutException, ConnectionError) as e:
# # # #                 logger.warning(f"Попытка {attempt + 1}/{retries} не удалась: {e}")
# # # #                 self.restart_driver()
# # # #                 self.random_delay(1, 3)  # Большая задержка перед повторной попыткой
# # # #         return False
# # # #
# # # #     def restart_driver(self):
# # # #         """Перезапуск драйвера при ошибке"""
# # # #         try:
# # # #             if self.driver:
# # # #                 self.driver.quit()
# # # #         except:
# # # #             pass
# # # #         self.driver = self.init_driver()
# # # #         logger.info("Драйвер перезапущен")
# # # #
# # # #     def get_product_links_from_page(self, page_num):
# # # #         """Собирает ссылки на продукты с одной страницы"""
# # # #         url = f"{self.base_url}?p={page_num}"
# # # #         logger.info(f"📄 Обрабатываю страницу {page_num}: {url}")
# # # #
# # # #         try:
# # # #             if not self.safe_get(url):
# # # #                 logger.error(f"Не удалось загрузить страницу {page_num}")
# # # #                 return 0
# # # #
# # # #             # Ищем все ссылки на странице
# # # #             all_links = self.driver.find_elements(By.TAG_NAME, "a")
# # # #
# # # #             page_links = []
# # # #             for link in all_links:
# # # #                 try:
# # # #                     href = link.get_attribute('href')
# # # #                     if not href:
# # # #                         continue
# # # #
# # # #                     clean_href = href.split('?')[0]
# # # #
# # # #                     # Проверяем, что это ссылка на продукт
# # # #                     if ('goldapple.ru' in clean_href and
# # # #                             '/parfjumerija' not in clean_href and
# # # #                             re.search(r'/\d+-[a-z0-9-]+$', clean_href, re.IGNORECASE)):
# # # #
# # # #                         if clean_href not in self.product_links:
# # # #                             page_links.append(clean_href)
# # # #                             self.product_links.add(clean_href)
# # # #                 except:
# # # #                     continue
# # # #
# # # #             logger.info(f"✅ Найдено {len(page_links)} новых ссылок на странице {page_num}")
# # # #
# # # #             if page_links and self.test_mode:
# # # #                 logger.info(f"   Примеры ссылок: {page_links[:3]}")
# # # #
# # # #             return len(page_links)
# # # #
# # # #         except Exception as e:
# # # #             logger.error(f"Ошибка на странице {page_num}: {e}")
# # # #             self.restart_driver()
# # # #             return 0
# # # #
# # # #     def get_total_pages(self, max_pages=500):
# # # #         """Определяет общее количество страниц"""
# # # #         # В тестовом режиме обрабатываем только 3 страницы
# # # #         if self.test_mode:
# # # #             test_pages = 3
# # # #             logger.info(f"🔧 Тестовый режим: обрабатываем {test_pages} страниц")
# # # #             return test_pages
# # # #
# # # #         try:
# # # #             if not self.safe_get(self.base_url):
# # # #                 return max_pages
# # # #
# # # #             # Ищем пагинацию
# # # #             try:
# # # #                 pagination = self.driver.find_element(By.CSS_SELECTOR, "ul._ga-plp-pagination_1ert2_1")
# # # #                 pagination_text = pagination.text
# # # #                 numbers = re.findall(r'\d+', pagination_text)
# # # #                 if numbers:
# # # #                     last_page = max(int(n) for n in numbers)
# # # #                     logger.info(f"📑 Всего страниц: {last_page}")
# # # #                     return min(last_page, max_pages)
# # # #             except:
# # # #                 pass
# # # #
# # # #         except Exception as e:
# # # #             logger.error(f"Не удалось определить количество страниц: {e}")
# # # #
# # # #         logger.info(f"Используем максимальное количество страниц: {max_pages}")
# # # #         return max_pages
# # # #
# # # #     def collect_all_products(self, max_pages=500, start_page=1, save_every=50):
# # # #         """Собирает ссылки на все продукты"""
# # # #         self.driver = self.init_driver()
# # # #
# # # #         try:
# # # #             total_pages = self.get_total_pages(max_pages)
# # # #             consecutive_errors = 0
# # # #
# # # #             for page in range(start_page, total_pages + 1):
# # # #                 try:
# # # #                     # Случайная задержка между страницами (0.3-1.5 секунды)
# # # #                     self.random_delay(0.3, 1.5)
# # # #
# # # #                     found = self.get_product_links_from_page(page)
# # # #
# # # #                     if found == 0:
# # # #                         consecutive_errors += 1
# # # #                         if consecutive_errors >= 5:
# # # #                             logger.warning(f"⚠️ 5 страниц подряд без ссылок, останавливаюсь на странице {page}")
# # # #                             break
# # # #                     else:
# # # #                         consecutive_errors = 0
# # # #
# # # #                     # Промежуточное сохранение (только в обычном режиме)
# # # #                     if not self.test_mode and page % save_every == 0:
# # # #                         self.save_to_csv(f"goldapple_perfumes_progress_{page}.csv", save_only=True)
# # # #                         logger.info(f"💾 Промежуточное сохранение на странице {page}: {len(self.product_links)} ссылок")
# # # #
# # # #                     # В тестовом режиме выводим прогресс после каждой страницы
# # # #                     if self.test_mode:
# # # #                         logger.info(
# # # #                             f"📊 Прогресс: страница {page}/{total_pages}, собрано {len(self.product_links)} ссылок")
# # # #
# # # #                 except Exception as e:
# # # #                     logger.error(f"Критическая ошибка на странице {page}: {e}")
# # # #                     self.restart_driver()
# # # #                     consecutive_errors += 1
# # # #
# # # #                     if consecutive_errors >= 3:
# # # #                         logger.error("❌ Слишком много ошибок подряд, прерывание")
# # # #                         break
# # # #
# # # #             logger.info(f"🎉 Сбор завершён! Всего собрано {len(self.product_links)} уникальных ссылок")
# # # #             return list(self.product_links)
# # # #
# # # #         except Exception as e:
# # # #             logger.error(f"Ошибка при сборе ссылок: {e}")
# # # #             return list(self.product_links)
# # # #         finally:
# # # #             if self.driver:
# # # #                 self.driver.quit()
# # # #
# # # #     def save_to_csv(self, filename="goldapple_perfumes.csv", save_only=False):
# # # #         """Сохраняет ссылки в CSV файл"""
# # # #         if not save_only:
# # # #             product_links = self.collect_all_products()
# # # #         else:
# # # #             product_links = list(self.product_links)
# # # #
# # # #         if not product_links:
# # # #             logger.warning("⚠️ Нет ссылок для сохранения")
# # # #             return
# # # #
# # # #         headers = [
# # # #             "Ссылка на продукт",
# # # #             "Наименование",
# # # #             "Цена",
# # # #             "Рейтинг пользователей",
# # # #             "Описание продукта",
# # # #             "Инструкция по применению",
# # # #             "Страна-производитель"
# # # #         ]
# # # #
# # # #         with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
# # # #             writer = csv.DictWriter(csvfile, fieldnames=headers)
# # # #             writer.writeheader()
# # # #
# # # #             for link in product_links:
# # # #                 # Извлекаем название продукта из ссылки
# # # #                 product_slug = link.split('/')[-1]
# # # #                 if '-' in product_slug:
# # # #                     # Убираем ID в начале
# # # #                     product_name = product_slug.split('-', 1)[1].replace('-', ' ').title()
# # # #                 else:
# # # #                     product_name = product_slug.replace('-', ' ').title()
# # # #
# # # #                 writer.writerow({
# # # #                     "Ссылка на продукт": link,
# # # #                     "Наименование": product_name,
# # # #                     "Цена": "",
# # # #                     "Рейтинг пользователей": "",
# # # #                     "Описание продукта": "",
# # # #                     "Инструкция по применению": "",
# # # #                     "Страна-производитель": ""
# # # #                 })
# # # #
# # # #         logger.info(f"💾 CSV файл '{filename}' успешно создан! Записей: {len(product_links)}")
# # # #
# # # #
# # # #
# # # # # import csv
# # # # # import time
# # # # # import re
# # # # # from selenium import webdriver
# # # # # from selenium.webdriver.chrome.options import Options
# # # # # from selenium.webdriver.common.by import By
# # # # # from selenium.webdriver.support.ui import WebDriverWait
# # # # # from selenium.webdriver.support import expected_conditions as EC
# # # # #
# # # # #
# # # # # class Parser:
# # # # #     def __init__(self, base_url):
# # # # #         self.base_url = base_url
# # # # #         self.product_links = set()
# # # # #         self.driver = None
# # # # #
# # # # #     def init_driver(self):
# # # # #         """Инициализация драйвера"""
# # # # #         chrome_options = Options()
# # # # #         chrome_options.add_argument("--headless")
# # # # #         chrome_options.add_argument("--no-sandbox")
# # # # #         chrome_options.add_argument("--disable-dev-shm-usage")
# # # # #         chrome_options.add_argument("--window-size=1920,1080")
# # # # #
# # # # #         self.driver = webdriver.Chrome(options=chrome_options)
# # # # #
# # # # #     def get_product_links_from_page(self, page_num):
# # # # #         """Собирает ссылки на продукты с одной страницы"""
# # # # #         url = f"{self.base_url}?p={page_num}"
# # # # #         print(f"  Обрабатываю страницу {page_num}: {url}")
# # # # #
# # # # #         try:
# # # # #             self.driver.get(url)
# # # # #             time.sleep(3)  # Ждём загрузки
# # # # #
# # # # #             # Способ 1: Ищем все ссылки, которые содержат ID продукта (цифры и дефис)
# # # # #             # Пример: /26662200001-vanilla-vibes
# # # # #             all_links = self.driver.find_elements(By.TAG_NAME, "a")
# # # # #
# # # # #             page_links = []
# # # # #             for link in all_links:
# # # # #                 href = link.get_attribute('href')
# # # # #                 if href:
# # # # #                     # Очищаем от параметров
# # # # #                     clean_href = href.split('?')[0]
# # # # #
# # # # #                     # Проверяем, что это ссылка на продукт:
# # # # #                     # 1. Содержит домен goldapple.ru
# # # # #                     # 2. В конце есть ID-продукта (цифры) и название через дефис
# # # # #                     # 3. Не содержит /parfjumerija (это категория, не продукт)
# # # # #                     if ('goldapple.ru' in clean_href and
# # # # #                             '/' in clean_href and
# # # # #                             '/parfjumerija' not in clean_href and
# # # # #                             re.search(r'/\d+-[a-z0-9-]+$', clean_href, re.IGNORECASE)):
# # # # #
# # # # #                         if clean_href not in self.product_links:
# # # # #                             page_links.append(clean_href)
# # # # #                             self.product_links.add(clean_href)
# # # # #
# # # # #             print(f"    Найдено {len(page_links)} новых ссылок на странице {page_num}")
# # # # #
# # # # #             # Для отладки: выводим первые 5 найденных ссылок
# # # # #             if page_links:
# # # # #                 print(f"    Примеры ссылок: {page_links[:3]}")
# # # # #
# # # # #             return len(page_links)
# # # # #
# # # # #         except Exception as e:
# # # # #             print(f"    Ошибка на странице {page_num}: {e}")
# # # # #             return 0
# # # # #
# # # # #     def get_total_pages(self, max_pages=500):
# # # # #         """Определяет общее количество страниц"""
# # # # #         try:
# # # # #             self.driver.get(self.base_url)
# # # # #             time.sleep(3)
# # # # #
# # # # #             # Ищем пагинацию
# # # # #             pagination_text = self.driver.find_element(By.CSS_SELECTOR, "ul._ga-plp-pagination_1ert2_1").text
# # # # #             numbers = re.findall(r'\d+', pagination_text)
# # # # #             if numbers:
# # # # #                 last_page = max(int(n) for n in numbers)
# # # # #                 print(f"Всего страниц: {last_page}")
# # # # #                 return min(last_page, max_pages)
# # # # #
# # # # #         except Exception as e:
# # # # #             print(f"Не удалось определить количество страниц: {e}")
# # # # #
# # # # #         print(f"Используем максимальное количество страниц: {max_pages}")
# # # # #         return max_pages
# # # # #
# # # # #     def collect_all_products(self, max_pages=500):
# # # # #         """Собирает ссылки на все продукты из раздела Парфюмерия"""
# # # # #         self.init_driver()
# # # # #
# # # # #         try:
# # # # #             total_pages = self.get_total_pages(max_pages)
# # # # #
# # # # #             for page in range(1, min(total_pages, max_pages) + 1):
# # # # #                 found = self.get_product_links_from_page(page)
# # # # #
# # # # #                 # Если на странице ничего не найдено, возможно, пагинация закончилась
# # # # #                 if found == 0 and page > 1:
# # # # #                     print(f"  На странице {page} не найдено ссылок, возможно, это конец")
# # # # #                     # Продолжаем, но если на 3х страницах подряд 0 - останавливаемся
# # # # #
# # # # #                 time.sleep(1)  # Вежливость к серверу
# # # # #
# # # # #                 if page % 10 == 0:
# # # # #                     print(f"Прогресс: {page}/{total_pages} страниц, собрано {len(self.product_links)} ссылок")
# # # # #
# # # # #         except Exception as e:
# # # # #             print(f"Ошибка при сборе ссылок: {e}")
# # # # #         finally:
# # # # #             self.driver.quit()
# # # # #
# # # # #         print(f"\n✅ Сбор завершён! Всего собрано {len(self.product_links)} уникальных ссылок на продукты")
# # # # #         return list(self.product_links)
# # # # #
# # # # #     def save_to_csv(self, filename="goldapple_perfumes.csv", max_pages=500):
# # # # #         """Сохраняет ссылки в CSV файл"""
# # # # #         product_links = self.collect_all_products(max_pages)
# # # # #
# # # # #         # Заголовки CSV
# # # # #         headers = [
# # # # #             "Ссылка на продукт",
# # # # #             "Наименование",
# # # # #             "Цена",
# # # # #             "Рейтинг пользователей",
# # # # #             "Описание продукта",
# # # # #             "Инструкция по применению",
# # # # #             "Страна-производитель"
# # # # #         ]
# # # # #
# # # # #         with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
# # # # #             writer = csv.DictWriter(csvfile, fieldnames=headers)
# # # # #             writer.writeheader()
# # # # #
# # # # #             for link in product_links:
# # # # #                 # Извлекаем название продукта из ссылки
# # # # #                 # Ссылка вида: https://goldapple.ru/26662200001-vanilla-vibes
# # # # #                 product_slug = link.split('/')[-1]
# # # # #                 if '-' in product_slug:
# # # # #                     # Убираем ID в начале
# # # # #                     product_name = product_slug.split('-', 1)[1].replace('-', ' ').title()
# # # # #                 else:
# # # # #                     product_name = product_slug.replace('-', ' ').title()
# # # # #
# # # # #                 writer.writerow({
# # # # #                     "Ссылка на продукт": link,
# # # # #                     "Наименование": product_name,
# # # # #                     "Цена": "",
# # # # #                     "Рейтинг пользователей": "",
# # # # #                     "Описание продукта": "",
# # # # #                     "Инструкция по применению": "",
# # # # #                     "Страна-производитель": ""
# # # # #                 })
# # # # #
# # # # #         print(f"\n✅ CSV файл '{filename}' успешно создан!")
# # # # #         print(f"   Всего записей: {len(product_links)}")
# # # # #
# # # # #
# # # # #
# # # # #
# # # # # # import csv
# # # # # # import time
# # # # # # from selenium import webdriver
# # # # # # from selenium.webdriver.chrome.options import Options
# # # # # # from selenium.webdriver.common.by import By
# # # # # # from selenium.webdriver.support.ui import WebDriverWait
# # # # # # from selenium.webdriver.support import expected_conditions as EC
# # # # # #
# # # # # #
# # # # # # class Parser:
# # # # # #     def __init__(self, base_url):
# # # # # #         self.base_url = base_url
# # # # # #         self.product_links = set()  # Используем set для уникальности
# # # # # #         self.driver = None
# # # # # #
# # # # # #     def init_driver(self):
# # # # # #         """Инициализация драйвера"""
# # # # # #         chrome_options = Options()
# # # # # #         chrome_options.add_argument("--headless")
# # # # # #         chrome_options.add_argument("--no-sandbox")
# # # # # #         chrome_options.add_argument("--disable-dev-shm-usage")
# # # # # #         chrome_options.add_argument("--window-size=1920,1080")
# # # # # #         # Ускоряем загрузку
# # # # # #         chrome_options.add_argument("--disable-images")
# # # # # #         chrome_options.add_argument("--disable-javascript")  # Не отключать, но можно ограничить
# # # # # #         chrome_options.add_experimental_option("prefs", {
# # # # # #             "profile.managed_default_content_settings.images": 2,  # Отключаем изображения
# # # # # #         })
# # # # # #
# # # # # #         self.driver = webdriver.Chrome(options=chrome_options)
# # # # # #
# # # # # #     def get_product_links_from_page(self, page_num):
# # # # # #         """Собирает ссылки на продукты с одной страницы"""
# # # # # #         url = f"{self.base_url}?p={page_num}"
# # # # # #         print(f"  Обрабатываю страницу {page_num}: {url}")
# # # # # #
# # # # # #         try:
# # # # # #             self.driver.get(url)
# # # # # #             # Ждём загрузки карточек товаров
# # # # # #             wait = WebDriverWait(self.driver, 10)
# # # # # #             wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='-']")))
# # # # # #
# # # # # #             # Небольшая задержка для полной загрузки
# # # # # #             time.sleep(2)
# # # # # #
# # # # # #             # Находим все ссылки на продукты
# # # # # #             # Ссылки обычно содержат ID продукта и название через дефис
# # # # # #             links = self.driver.find_elements(By.CSS_SELECTOR, "a._ga-product-card-vertical__link")
# # # # # #
# # # # # #             page_links = []
# # # # # #             for link in links:
# # # # # #                 href = link.get_attribute('href')
# # # # # #                 if href and '/parfjumerija' not in href and href not in self.product_links:
# # # # # #                     # Очищаем ссылку от лишних параметров
# # # # # #                     clean_href = href.split('?')[0]
# # # # # #                     page_links.append(clean_href)
# # # # # #                     self.product_links.add(clean_href)
# # # # # #
# # # # # #             print(f"    Найдено {len(page_links)} новых ссылок на странице {page_num}")
# # # # # #             return len(page_links)
# # # # # #
# # # # # #         except Exception as e:
# # # # # #             print(f"    Ошибка на странице {page_num}: {e}")
# # # # # #             return 0
# # # # # #
# # # # # #     def get_total_pages(self):
# # # # # #         """Определяет общее количество страниц"""
# # # # # #         try:
# # # # # #             self.driver.get(self.base_url)
# # # # # #             time.sleep(3)
# # # # # #
# # # # # #             # Ищем последнюю страницу в пагинации
# # # # # #             pagination_links = self.driver.find_elements(By.CSS_SELECTOR, "ul._ga-plp-pagination_1ert2_1 li a")
# # # # # #
# # # # # #             last_page = 1
# # # # # #             for link in pagination_links:
# # # # # #                 href = link.get_attribute('href')
# # # # # #                 if href and 'p=' in href:
# # # # # #                     try:
# # # # # #                         page_num = int(href.split('p=')[-1].split('&')[0])
# # # # # #                         if page_num > last_page:
# # # # # #                             last_page = page_num
# # # # # #                     except:
# # # # # #                         pass
# # # # # #
# # # # # #             # Также проверяем последний li без ссылки (текущая страница)
# # # # # #             page_items = self.driver.find_elements(By.CSS_SELECTOR, "ul._ga-plp-pagination_1ert2_1 li")
# # # # # #             for item in page_items:
# # # # # #                 text = item.text.strip()
# # # # # #                 if text.isdigit() and int(text) > last_page:
# # # # # #                     last_page = int(text)
# # # # # #
# # # # # #             print(f"Всего страниц: {last_page}")
# # # # # #             return last_page
# # # # # #
# # # # # #         except Exception as e:
# # # # # #             print(f"Ошибка при определении количества страниц: {e}")
# # # # # #             return 500  # Если не получилось, проходим 500 страниц
# # # # # #
# # # # # #     def collect_all_products(self):
# # # # # #         """Собирает ссылки на все продукты из раздела Парфюмерия"""
# # # # # #         self.init_driver()
# # # # # #
# # # # # #         try:
# # # # # #             total_pages = 2  # ТЕСТОВЫЙ РЕЖИМ РАБОТАЕМ ТОЛЬКО НА 2+1 СТРАНИЦАХ !!!
# # # # # #             # total_pages = self.get_total_pages()
# # # # # #
# # # # # #             for page in range(1, total_pages + 1):
# # # # # #                 self.get_product_links_from_page(page)
# # # # # #                 # Небольшая задержка между запросами, чтобы не нагружать сервер
# # # # # #                 time.sleep(3)  # СДЕЛАТЬ СЛУЧАЙНОЙ ПОТОМ
# # # # # #
# # # # # #                 # # Выводим прогресс каждые 10 страниц
# # # # # #                 # if page % 10 == 0:
# # # # # #                 #     print(f"Прогресс: {page}/{total_pages} страниц, собрано {len(self.product_links)} ссылок")
# # # # # #                 print(f"Прогресс: {page}/{total_pages} страниц, собрано {len(self.product_links)} ссылок")  # ВРЕМЕННО
# # # # # #
# # # # # #         except Exception as e:
# # # # # #             print(f"Ошибка при сборе ссылок: {e}")
# # # # # #         finally:
# # # # # #             self.driver.quit()
# # # # # #
# # # # # #         print(f"\n✅ Сбор завершён! Всего собрано {len(self.product_links)} уникальных ссылок на продукты")
# # # # # #         return list(self.product_links)
# # # # # #
# # # # # #     def save_to_csv(self, filename="goldapple_perfumes.csv"):
# # # # # #         """Сохраняет ссылки в CSV файл"""
# # # # # #         product_links = self.collect_all_products()
# # # # # #
# # # # # #         # Заголовки CSV
# # # # # #         headers = [
# # # # # #             "Ссылка на продукт",
# # # # # #             "Наименование",
# # # # # #             "Цена",
# # # # # #             "Рейтинг пользователей",
# # # # # #             "Описание продукта",
# # # # # #             "Инструкция по применению",
# # # # # #             "Страна-производитель"
# # # # # #         ]
# # # # # #
# # # # # #         with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
# # # # # #             writer = csv.DictWriter(csvfile, fieldnames=headers)
# # # # # #             writer.writeheader()
# # # # # #
# # # # # #             for link in product_links:
# # # # # #                 # Извлекаем название продукта из ссылки
# # # # # #                 # Ссылка вида: https://goldapple.ru/26662200001-vanilla-vibes
# # # # # #                 product_name = link.split('/')[-1] if '/' in link else link
# # # # # #                 # Убираем ID в начале, если есть
# # # # # #                 if '-' in product_name:
# # # # # #                     product_name = product_name.split('-', 1)[1].replace('-', ' ').title()
# # # # # #
# # # # # #                 writer.writerow({
# # # # # #                     "Ссылка на продукт": link,
# # # # # #                     "Наименование": product_name,
# # # # # #                     "Цена": "",  # Будет заполнено при парсинге карточки товара
# # # # # #                     "Рейтинг пользователей": "",
# # # # # #                     "Описание продукта": "",
# # # # # #                     "Инструкция по применению": "",
# # # # # #                     "Страна-производитель": ""
# # # # # #                 })
# # # # # #
# # # # # #         print(f"\n✅ CSV файл '{filename}' успешно создан!")
# # # # # #         print(f"   Всего записей: {len(product_links)}")
# # # # # #
# # # # # #
# # # # # #
# # # # # #
# # # # # # # from selenium import webdriver
# # # # # # # from selenium.webdriver.chrome.options import Options
# # # # # # # import time
# # # # # # #
# # # # # # #
# # # # # # # class Parser:
# # # # # # #     def __init__(self, base_url):
# # # # # # #         self.base_url = base_url
# # # # # # #         self.target_product_href = "/26662200001-vanilla-vibes"
# # # # # # #
# # # # # # #     def find_product_url(self):
# # # # # # #         chrome_options = Options()
# # # # # # #         chrome_options.add_argument("--headless")
# # # # # # #         chrome_options.add_argument("--no-sandbox")
# # # # # # #         chrome_options.add_argument("--disable-dev-shm-usage")
# # # # # # #
# # # # # # #         driver = webdriver.Chrome(options=chrome_options)
# # # # # # #
# # # # # # #         try:
# # # # # # #             # Проверяем страницы с 1 по 500
# # # # # # #             for page in range(1, 501):
# # # # # # #                 url = f"{self.base_url}?p={page}"
# # # # # # #                 print(f"Проверяю страницу {page}: {url}")
# # # # # # #
# # # # # # #                 driver.get(url)
# # # # # # #                 time.sleep(3)  # Ждём загрузки
# # # # # # #
# # # # # # #                 # Ищем ссылку на товар
# # # # # # #                 links = driver.find_elements("css selector", f"a[href='{self.target_product_href}']")
# # # # # # #
# # # # # # #                 if links:
# # # # # # #                     full_url = f"https://goldapple.ru{self.target_product_href}"
# # # # # # #                     print(f"✅ Найдено на странице {page}: {full_url}")
# # # # # # #                     return full_url
# # # # # # #
# # # # # # #         except Exception as e:
# # # # # # #             print(f"Ошибка: {e}")
# # # # # # #             return None
# # # # # # #         finally:
# # # # # # #             driver.quit()
# # # # # # #
# # # # # # #
# # # # # # # # # Использование
# # # # # # # # parser = Parser("https://goldapple.ru/parfjumerija")
# # # # # # # # product_url = parser.find_product_url()
# # # # # # # # print(product_url)
# # # # # # #
# # # # # # #
# # # # # # #
# # # # # # #
# # # # # # #
# # # # # # #
# # # # # # #
# # # # # # #
# # # # # # #
# # # # # # #
# # # # # # #
# # # # # # #
# # # # # # #
# # # # # # # # import requests
# # # # # # # # from src.product import Product
# # # # # # # # # from bs4 import BeautifulSoup
# # # # # # # # import re
# # # # # # # # # import time
# # # # # # # #
# # # # # # # # from selenium import webdriver
# # # # # # # # from selenium.webdriver.chrome.options import Options
# # # # # # # # import time
# # # # # # # #
# # # # # # # #
# # # # # # # # # использованы АКУТАЛЬНЫЕ селекторы полей
# # # # # # # # class Parser:
# # # # # # # #     def __init__(self, url):
# # # # # # # #         # self.url = "https://goldapple.ru/parfjumerija"
# # # # # # # #         self.url = url
# # # # # # # #         self.session = requests.Session()
# # # # # # # #         self.session.headers.update({
# # # # # # # #             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
# # # # # # # #         })
# # # # # # # #
# # # # # # # #     def fetch_page(self):
# # # # # # # #         # Настраиваем опции Chrome (можно сделать headless для фоновой работы)
# # # # # # # #         chrome_options = Options()
# # # # # # # #         chrome_options.add_argument("--headless")  # Фоновый режим (без открытия окна браузера)
# # # # # # # #         # Отключает sandbox (изолированную среду) Chrome - — необходимо для Docker и сред с ограниченными правами
# # # # # # # #         # Нужно для запуска в контейнерах (Docker) и виртуальных машинах, где могут быть ограничения прав.
# # # # # # # #         chrome_options.add_argument("--no-sandbox")
# # # # # # # #         # Используем /tmp вместо /dev/shm — решаем проблему ограниченного объёма памяти в Docker
# # # # # # # #         chrome_options.add_argument("--disable-dev-shm-usage")
# # # # # # # #
# # # # # # # #         # Создаём драйвер
# # # # # # # #         driver = webdriver.Chrome(options=chrome_options)
# # # # # # # #
# # # # # # # #         try:
# # # # # # # #             # Открываем страницу
# # # # # # # #             driver.get(self.url)
# # # # # # # #
# # # # # # # #             # Даём время на загрузку и выполнение JavaScript
# # # # # # # #             time.sleep(15)  # Можно увеличить, если товары подгружаются дольше
# # # # # # # #
# # # # # # # #             # Получаем полностью отрендеренный HTML
# # # # # # # #             html_content = driver.page_source
# # # # # # # #
# # # # # # # #             # Сохраняем HTML в файл
# # # # # # # #             with open('page.html', 'w', encoding='utf-8') as file:
# # # # # # # #                 file.write(html_content)
# # # # # # # #
# # # # # # # #             print("HTML-код сохранён в файл 'page.html'")
# # # # # # # #
# # # # # # # #             return html_content
# # # # # # # #
# # # # # # # #         except Exception as e:
# # # # # # # #             print(f"Ошибка при загрузке страницы: {e}")
# # # # # # # #             return None
# # # # # # # #         finally:
# # # # # # # #             # Обязательно закрываем драйвер
# # # # # # # #             driver.quit()
# # # # # # # #
# # # # # # # #     # def fetch_page(self):
# # # # # # # #     #     response = self.session.get(self.url, timeout=10)
# # # # # # # #     #     response.raise_for_status()
# # # # # # # #     #     html_content = response.text  # Сохраняем HTML в переменную
# # # # # # # #     #     # Сохраняем HTML в файл
# # # # # # # #     #     with open('page.html', 'w', encoding='utf-8') as file:
# # # # # # # #     #         file.write(html_content)
# # # # # # # #     #     print("HTML-код сохранён в файл 'page.html'")  # Опциональный вывод в консоль
# # # # # # # #     #     # print("HTML-код страницы:")
# # # # # # # #     #     # print(html_content)  # Выводим в консоль
# # # # # # # #     #     return html_content  # Возвращаем строку HTML, а не BeautifulSoup
# # # # # # # #     #     # return response.text  # Возвращаем строку HTML, а не BeautifulSoup
# # # # # # # #     #     # return BeautifulSoup(response.content, 'html.parser')
# # # # # # # #
# # # # # # # #     @staticmethod
# # # # # # # #     def parse_product_list(html_content):
# # # # # # # #     # def parse_product_list(soup):
# # # # # # # #         """Парсинг списка товаров на странице каталога — извлекаем URL товаров"""
# # # # # # # #         products = []  # Инициализируем пустой список для хранения данных о товарах
# # # # # # # #
# # # # # # # #         # Регулярное выражение для поиска <link itemprop="url" href="...">
# # # # # # # #         # Ищет href, начинающийся с https://goldapple.ru/
# # # # # # # #         pattern = r'<link\s+itemprop=[""]url[""]\s+href=[""](https://goldapple.ru/\d+-\w+)[""]'
# # # # # # # #
# # # # # # # #         # Находим все совпадения в HTML-строке
# # # # # # # #         matches = re.findall(pattern, html_content, re.IGNORECASE)
# # # # # # # #
# # # # # # # #         print("Найденные URL (регулярные выражения):")
# # # # # # # #         print(matches)
# # # # # # # #
# # # # # # # #         # Формируем список товаров
# # # # # # # #         for url in matches:
# # # # # # # #             products.append({
# # # # # # # #                 'url': url
# # # # # # # #             })
# # # # # # # #
# # # # # # # #         print("Итоговый список товаров (products):")
# # # # # # # #         print(products)
# # # # # # # #
# # # # # # # #         return products
# # # # # # # #
# # # # # # # #
# # # # # # # #
# # # # # # # #
# # # # # # # #         # # Если ссылки на продукты лежат в тегах <link itemprop="url">
# # # # # # # #         # product_links = soup.select('link[itemprop="url"][href^="https://goldapple.ru/"]')
# # # # # # # #         #
# # # # # # # #         # # Выводим итоговый список products в консоль
# # # # # # # #         # print("Итоговый список ссылок на продукты (product_links):")
# # # # # # # #         # print(product_links)
# # # # # # # #         #
# # # # # # # #         # for link in product_links:
# # # # # # # #         #     href = link['href']  # Получаем значение href
# # # # # # # #         #     product_url = href  # Здесь уже полный URL, префикс добавлять не нужно
# # # # # # # #         #
# # # # # # # #         #     # # Извлекаем название (если оно есть в атрибутах или тексте)
# # # # # # # #         #     # name = link.get('title', 'Не указано')  # Пример — если название в title
# # # # # # # #         #
# # # # # # # #         #     # Далее — формируем словарь с данными о товаре, как сейчас
# # # # # # # #         #     products.append({
# # # # # # # #         #         'url': product_url,
# # # # # # # #         #         # 'name': name,
# # # # # # # #         #         # 'price': '0',  # Цена пока неизвестна — парсится на детальной странице
# # # # # # # #         #         # 'rating': '0'  # Рейтинг пока неизвестен
# # # # # # # #         #     })
# # # # # # # #         #
# # # # # # # #         # # Выводим итоговый список products в консоль
# # # # # # # #         # print("Итоговый список товаров (products):")
# # # # # # # #         # print(products)
# # # # # # # #         #
# # # # # # # #         # # cards = soup.select('a.product-card__link')  # Находим все ссылки с карточками товаров по CSS‑селектору
# # # # # # # #         #
# # # # # # # #         # # for card in cards:  # Перебираем каждую карточку товара в найденном списке
# # # # # # # #         # #     # Извлекаем URL товара
# # # # # # # #         # #     href = card.get('href')  # Получаем значение атрибута 'href' из тега <a>
# # # # # # # #         # #     if not href:  # Проверяем, существует ли атрибут href
# # # # # # # #         # #         continue  # Если href отсутствует, пропускаем текущую итерацию цикла — переходим к следующей карточке
# # # # # # # #         # #
# # # # # # # #         # #     # Формируем полный URL товара:
# # # # # # # #         # #     # Если ссылка относительная (начинается с '/'), добавляем базовый домен
# # # # # # # #         # #     # В противном случае используем ссылку как есть
# # # # # # # #         # #     product_url = 'https://goldapple.ru' + href if href.startswith('/') else href
# # # # # # # #         # #     # product_url = 'https://goldapple.ru' + card['href']
# # # # # # # #         # #
# # # # # # # #         # #     # Извлекаем название товара (если доступно)
# # # # # # # #         # #     name_elem = card.select_one('span.product-card__name')  # Ищем элемент с названием товара внутри карточки
# # # # # # # #         # #     # Если элемент найден, берём его текст и убираем лишние пробелы; иначе — ставим заглушку
# # # # # # # #         # #     name = name_elem.text.strip() if name_elem else 'Не указано'
# # # # # # # #         # #
# # # # # # # #         # #     # Извлекаем цену товара (если доступна)
# # # # # # # #         # #     price_elem = card.select_one('span.current-price')  # Ищем элемент с текущей ценой
# # # # # # # #         # #     # Если элемент найден, удаляем все нецифровые символы из текста (оставляем только цифры цены);
# # # # # # # #         # #     # иначе устанавливаем цену '0'
# # # # # # # #         # #     price = re.sub(r'\D', '', price_elem.text) if price_elem else '0'
# # # # # # # #         # #
# # # # # # # #         # #     # Извлекаем рейтинг товара (если доступен)
# # # # # # # #         # #     rating_elem = card.select_one('div.rating__stars')  # Ищем элемент со звездой рейтинга
# # # # # # # #         # #     # Если элемент найден, получаем значение атрибута 'data-rating'; иначе — ставим '0'
# # # # # # # #         # #     rating = rating_elem.get('data-rating', '0') if rating_elem else '0'
# # # # # # # #         # #
# # # # # # # #         # #     # name = name_elem.text.strip() if name_elem else 'Не указано'
# # # # # # # #         # #     # price = re.sub(r'\D', '', price_elem.text) if price_elem else '0'
# # # # # # # #         # #     # rating = rating_elem['data-rating'] if rating_elem and rating_elem.get('data-rating') else '0'
# # # # # # # #         # #
# # # # # # # #         # #     # Добавляем словарь с данными о текущем товаре в общий список
# # # # # # # #         # #     products.append({
# # # # # # # #         # #         'url': product_url,  # URL страницы товара
# # # # # # # #         # #         'name': name,  # Название товара
# # # # # # # #         # #         'price': price,  # Цена (только цифры)
# # # # # # # #         # #         'rating': rating  # Рейтинг (значение из data-rating)
# # # # # # # #         # #     })
# # # # # # # #         # return products  # Возвращаем список словарей с информацией о всех найденных товарах
# # # # # # # #
# # # # # # # #     def parse_product_detail(self, soup, product_url="https://goldapple.ru/99000128231-parfumernaa-voda-love-republic-black-10ml"):
# # # # # # # #         """Парсинг детальной информации о товаре"""
# # # # # # # #
# # # # # # # #         # на будущую модель
# # # # # # # #         # soup.select_one('_ga-pdp-tabs-content_sub-title_96ko0_247').text  # артикул
# # # # # # # #
# # # # # # # #         # Наименование (полное)
# # # # # # # #         name_elem = soup.select_one('_ga-pdp-tabs-content_title_96ko0_109').text  # название
# # # # # # # #         # name_elem = soup.select_one('h1.product-main__title')
# # # # # # # #         name = name_elem.text.strip() if name_elem else 'Не указано'
# # # # # # # #
# # # # # # # #         # Цена
# # # # # # # #         price_elem = soup.select_one('span.current-price, div.price__current')
# # # # # # # #         price = re.sub(r'\D', '', price_elem.text) if price_elem else '0'
# # # # # # # #
# # # # # # # #         # Описание
# # # # # # # #         desc_elem = soup.select_one('_ga-pdp-wysiwyg_rmnt6_55[itemprop="description"]').text  # описание
# # # # # # # #         # desc_elem = soup.select_one('div.product-description__content')
# # # # # # # #         description = desc_elem.get_text(strip=True) if desc_elem else 'Нет описания'
# # # # # # # #
# # # # # # # #         # Инструкция по применению
# # # # # # # #         instruction_header = soup.find('h3', string=re.compile(r'Способ применения', re.IGNORECASE))
# # # # # # # #         instructions = 'Нет инструкции'
# # # # # # # #         if instruction_header:
# # # # # # # #             next_elem = instruction_header.find_next('div')
# # # # # # # #             if next_elem:
# # # # # # # #                 instructions = next_elem.get_text(strip=True)
# # # # # # # #
# # # # # # # #         # Страна-производитель
# # # # # # # #         country_elem = soup.find('span', string=re.compile(r'Страна производства', re.IGNORECASE))
# # # # # # # #         country = 'Не указано'
# # # # # # # #         if country_elem:
# # # # # # # #             # Ищем следующий элемент с информацией
# # # # # # # #             country_value = country_elem.find_next('span')
# # # # # # # #             if country_value:
# # # # # # # #                 country = country_value.get_text(strip=True)
# # # # # # # #
# # # # # # # #         return Product(
# # # # # # # #             url=product_url,
# # # # # # # #             name=name,
# # # # # # # #             price=price,
# # # # # # # #             rating=self._get_rating_from_detail(soup),
# # # # # # # #             description=description,
# # # # # # # #             instructions=instructions,
# # # # # # # #             country=country
# # # # # # # #         )
# # # # # # # #
# # # # # # # #     @staticmethod
# # # # # # # #     def _get_rating_from_detail(soup):
# # # # # # # #         """Извлечение рейтинга со страницы товара"""
# # # # # # # #         rating_elem = soup.select_one('div.rating__value')
# # # # # # # #         if rating_elem:
# # # # # # # #             rating_text = rating_elem.get_text()
# # # # # # # #             match = re.search(r'\d+\.?\d*', rating_text)
# # # # # # # #             return match.group() if match else '0'
# # # # # # # #         return '0'
# # # # # #
# # # # # #
# # # # # #
# # # # # #
# # # # # #
# # # # # #
# # # # # #
# # # # # # # import csv
# # # # # # # import time
# # # # # # # from selenium import webdriver
# # # # # # # from selenium.webdriver.chrome.options import Options
# # # # # # # from selenium.webdriver.common.by import By
# # # # # # # from selenium.webdriver.support.ui import WebDriverWait
# # # # # # # from selenium.webdriver.support import expected_conditions as EC
# # # # # # #
# # # # # # #
# # # # # # # class Parser:
# # # # # # #     def __init__(self, base_url):
# # # # # # #         self.base_url = base_url
# # # # # # #         self.product_links = set()  # Используем set для уникальности
# # # # # # #         self.driver = None
# # # # # # #
# # # # # # #     def init_driver(self):
# # # # # # #         """Инициализация драйвера"""
# # # # # # #         chrome_options = Options()
# # # # # # #         chrome_options.add_argument("--headless")
# # # # # # #         chrome_options.add_argument("--no-sandbox")
# # # # # # #         chrome_options.add_argument("--disable-dev-shm-usage")
# # # # # # #         chrome_options.add_argument("--window-size=1920,1080")
# # # # # # #         # Ускоряем загрузку
# # # # # # #         chrome_options.add_argument("--disable-images")
# # # # # # #         chrome_options.add_argument("--disable-javascript")  # Не отключать, но можно ограничить
# # # # # # #         chrome_options.add_experimental_option("prefs", {
# # # # # # #             "profile.managed_default_content_settings.images": 2,  # Отключаем изображения
# # # # # # #         })
# # # # # # #
# # # # # # #         self.driver = webdriver.Chrome(options=chrome_options)
# # # # # # #
# # # # # # #     def get_product_links_from_page(self, page_num):
# # # # # # #         """Собирает ссылки на продукты с одной страницы"""
# # # # # # #         url = f"{self.base_url}?p={page_num}"
# # # # # # #         print(f"  Обрабатываю страницу {page_num}: {url}")
# # # # # # #
# # # # # # #         try:
# # # # # # #             self.driver.get(url)
# # # # # # #             # Ждём загрузки карточек товаров
# # # # # # #             wait = WebDriverWait(self.driver, 10)
# # # # # # #             wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='-']")))
# # # # # # #
# # # # # # #             # Небольшая задержка для полной загрузки
# # # # # # #             time.sleep(2)
# # # # # # #
# # # # # # #             # Находим все ссылки на продукты
# # # # # # #             # Ссылки обычно содержат ID продукта и название через дефис
# # # # # # #             links = self.driver.find_elements(By.CSS_SELECTOR, "a._ga-product-card-vertical__link")
# # # # # # #
# # # # # # #             page_links = []
# # # # # # #             for link in links:
# # # # # # #                 href = link.get_attribute('href')
# # # # # # #                 if href and '/parfjumerija' not in href and href not in self.product_links:
# # # # # # #                     # Очищаем ссылку от лишних параметров
# # # # # # #                     clean_href = href.split('?')[0]
# # # # # # #                     page_links.append(clean_href)
# # # # # # #                     self.product_links.add(clean_href)
# # # # # # #
# # # # # # #             print(f"    Найдено {len(page_links)} новых ссылок на странице {page_num}")
# # # # # # #             return len(page_links)
# # # # # # #
# # # # # # #         except Exception as e:
# # # # # # #             print(f"    Ошибка на странице {page_num}: {e}")
# # # # # # #             return 0
# # # # # # #
# # # # # # #     def get_total_pages(self):
# # # # # # #         """Определяет общее количество страниц"""
# # # # # # #         try:
# # # # # # #             self.driver.get(self.base_url)
# # # # # # #             time.sleep(3)
# # # # # # #
# # # # # # #             # Ищем последнюю страницу в пагинации
# # # # # # #             pagination_links = self.driver.find_elements(By.CSS_SELECTOR, "ul._ga-plp-pagination_1ert2_1 li a")
# # # # # # #
# # # # # # #             last_page = 1
# # # # # # #             for link in pagination_links:
# # # # # # #                 href = link.get_attribute('href')
# # # # # # #                 if href and 'p=' in href:
# # # # # # #                     try:
# # # # # # #                         page_num = int(href.split('p=')[-1].split('&')[0])
# # # # # # #                         if page_num > last_page:
# # # # # # #                             last_page = page_num
# # # # # # #                     except:
# # # # # # #                         pass
# # # # # # #
# # # # # # #             # Также проверяем последний li без ссылки (текущая страница)
# # # # # # #             page_items = self.driver.find_elements(By.CSS_SELECTOR, "ul._ga-plp-pagination_1ert2_1 li")
# # # # # # #             for item in page_items:
# # # # # # #                 text = item.text.strip()
# # # # # # #                 if text.isdigit() and int(text) > last_page:
# # # # # # #                     last_page = int(text)
# # # # # # #
# # # # # # #             print(f"Всего страниц: {last_page}")
# # # # # # #             return last_page
# # # # # # #
# # # # # # #         except Exception as e:
# # # # # # #             print(f"Ошибка при определении количества страниц: {e}")
# # # # # # #             return 500  # Если не получилось, проходим 500 страниц
# # # # # # #
# # # # # # #     def collect_all_products(self):
# # # # # # #         """Собирает ссылки на все продукты из раздела Парфюмерия"""
# # # # # # #         self.init_driver()
# # # # # # #
# # # # # # #         try:
# # # # # # #             total_pages = 2  # ТЕСТОВЫЙ РЕЖИМ РАБОТАЕМ ТОЛЬКО НА 2+1 СТРАНИЦАХ !!!
# # # # # # #             # total_pages = self.get_total_pages()
# # # # # # #
# # # # # # #             for page in range(1, total_pages + 1):
# # # # # # #                 self.get_product_links_from_page(page)
# # # # # # #                 # Небольшая задержка между запросами, чтобы не нагружать сервер
# # # # # # #                 time.sleep(3)  # СДЕЛАТЬ СЛУЧАЙНОЙ ПОТОМ
# # # # # # #
# # # # # # #                 # # Выводим прогресс каждые 10 страниц
# # # # # # #                 # if page % 10 == 0:
# # # # # # #                 #     print(f"Прогресс: {page}/{total_pages} страниц, собрано {len(self.product_links)} ссылок")
# # # # # # #                 print(f"Прогресс: {page}/{total_pages} страниц, собрано {len(self.product_links)} ссылок")  # ВРЕМЕННО
# # # # # # #
# # # # # # #         except Exception as e:
# # # # # # #             print(f"Ошибка при сборе ссылок: {e}")
# # # # # # #         finally:
# # # # # # #             self.driver.quit()
# # # # # # #
# # # # # # #         print(f"\n✅ Сбор завершён! Всего собрано {len(self.product_links)} уникальных ссылок на продукты")
# # # # # # #         return list(self.product_links)
# # # # # # #
# # # # # # #     def save_to_csv(self, filename="goldapple_perfumes.csv"):
# # # # # # #         """Сохраняет ссылки в CSV файл"""
# # # # # # #         product_links = self.collect_all_products()
# # # # # # #
# # # # # # #         # Заголовки CSV
# # # # # # #         headers = [
# # # # # # #             "Ссылка на продукт",
# # # # # # #             "Наименование",
# # # # # # #             "Цена",
# # # # # # #             "Рейтинг пользователей",
# # # # # # #             "Описание продукта",
# # # # # # #             "Инструкция по применению",
# # # # # # #             "Страна-производитель"
# # # # # # #         ]
# # # # # # #
# # # # # # #         with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
# # # # # # #             writer = csv.DictWriter(csvfile, fieldnames=headers)
# # # # # # #             writer.writeheader()
# # # # # # #
# # # # # # #             for link in product_links:
# # # # # # #                 # Извлекаем название продукта из ссылки
# # # # # # #                 # Ссылка вида: https://goldapple.ru/26662200001-vanilla-vibes
# # # # # # #                 product_name = link.split('/')[-1] if '/' in link else link
# # # # # # #                 # Убираем ID в начале, если есть
# # # # # # #                 if '-' in product_name:
# # # # # # #                     product_name = product_name.split('-', 1)[1].replace('-', ' ').title()
# # # # # # #
# # # # # # #                 writer.writerow({
# # # # # # #                     "Ссылка на продукт": link,
# # # # # # #                     "Наименование": product_name,
# # # # # # #                     "Цена": "",  # Будет заполнено при парсинге карточки товара
# # # # # # #                     "Рейтинг пользователей": "",
# # # # # # #                     "Описание продукта": "",
# # # # # # #                     "Инструкция по применению": "",
# # # # # # #                     "Страна-производитель": ""
# # # # # # #                 })
# # # # # # #
# # # # # # #         print(f"\n✅ CSV файл '{filename}' успешно создан!")
# # # # # # #         print(f"   Всего записей: {len(product_links)}")
# # # # # # #
# # # # # # #
# # # # # # #
# # # # # # #
# # # # # # # # from selenium import webdriver
# # # # # # # # from selenium.webdriver.chrome.options import Options
# # # # # # # # import time
# # # # # # # #
# # # # # # # #
# # # # # # # # class Parser:
# # # # # # # #     def __init__(self, base_url):
# # # # # # # #         self.base_url = base_url
# # # # # # # #         self.target_product_href = "/26662200001-vanilla-vibes"
# # # # # # # #
# # # # # # # #     def find_product_url(self):
# # # # # # # #         chrome_options = Options()
# # # # # # # #         chrome_options.add_argument("--headless")
# # # # # # # #         chrome_options.add_argument("--no-sandbox")
# # # # # # # #         chrome_options.add_argument("--disable-dev-shm-usage")
# # # # # # # #
# # # # # # # #         driver = webdriver.Chrome(options=chrome_options)
# # # # # # # #
# # # # # # # #         try:
# # # # # # # #             # Проверяем страницы с 1 по 500
# # # # # # # #             for page in range(1, 501):
# # # # # # # #                 url = f"{self.base_url}?p={page}"
# # # # # # # #                 print(f"Проверяю страницу {page}: {url}")
# # # # # # # #
# # # # # # # #                 driver.get(url)
# # # # # # # #                 time.sleep(3)  # Ждём загрузки
# # # # # # # #
# # # # # # # #                 # Ищем ссылку на товар
# # # # # # # #                 links = driver.find_elements("css selector", f"a[href='{self.target_product_href}']")
# # # # # # # #
# # # # # # # #                 if links:
# # # # # # # #                     full_url = f"https://goldapple.ru{self.target_product_href}"
# # # # # # # #                     print(f"✅ Найдено на странице {page}: {full_url}")
# # # # # # # #                     return full_url
# # # # # # # #
# # # # # # # #         except Exception as e:
# # # # # # # #             print(f"Ошибка: {e}")
# # # # # # # #             return None
# # # # # # # #         finally:
# # # # # # # #             driver.quit()
# # # # # # # #
# # # # # # # #
# # # # # # # # # # Использование
# # # # # # # # # parser = Parser("https://goldapple.ru/parfjumerija")
# # # # # # # # # product_url = parser.find_product_url()
# # # # # # # # # print(product_url)
# # # # # # # #
# # # # # # # #
# # # # # # # #
# # # # # # # #
# # # # # # # #
# # # # # # # #
# # # # # # # #
# # # # # # # #
# # # # # # # #
# # # # # # # #
# # # # # # # #
# # # # # # # #
# # # # # # # #
# # # # # # # # # import requests
# # # # # # # # # from src.product import Product
# # # # # # # # # # from bs4 import BeautifulSoup
# # # # # # # # # import re
# # # # # # # # # # import time
# # # # # # # # #
# # # # # # # # # from selenium import webdriver
# # # # # # # # # from selenium.webdriver.chrome.options import Options
# # # # # # # # # import time
# # # # # # # # #
# # # # # # # # #
# # # # # # # # # # использованы АКУТАЛЬНЫЕ селекторы полей
# # # # # # # # # class Parser:
# # # # # # # # #     def __init__(self, url):
# # # # # # # # #         # self.url = "https://goldapple.ru/parfjumerija"
# # # # # # # # #         self.url = url
# # # # # # # # #         self.session = requests.Session()
# # # # # # # # #         self.session.headers.update({
# # # # # # # # #             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
# # # # # # # # #         })
# # # # # # # # #
# # # # # # # # #     def fetch_page(self):
# # # # # # # # #         # Настраиваем опции Chrome (можно сделать headless для фоновой работы)
# # # # # # # # #         chrome_options = Options()
# # # # # # # # #         chrome_options.add_argument("--headless")  # Фоновый режим (без открытия окна браузера)
# # # # # # # # #         # Отключает sandbox (изолированную среду) Chrome - — необходимо для Docker и сред с ограниченными правами
# # # # # # # # #         # Нужно для запуска в контейнерах (Docker) и виртуальных машинах, где могут быть ограничения прав.
# # # # # # # # #         chrome_options.add_argument("--no-sandbox")
# # # # # # # # #         # Используем /tmp вместо /dev/shm — решаем проблему ограниченного объёма памяти в Docker
# # # # # # # # #         chrome_options.add_argument("--disable-dev-shm-usage")
# # # # # # # # #
# # # # # # # # #         # Создаём драйвер
# # # # # # # # #         driver = webdriver.Chrome(options=chrome_options)
# # # # # # # # #
# # # # # # # # #         try:
# # # # # # # # #             # Открываем страницу
# # # # # # # # #             driver.get(self.url)
# # # # # # # # #
# # # # # # # # #             # Даём время на загрузку и выполнение JavaScript
# # # # # # # # #             time.sleep(15)  # Можно увеличить, если товары подгружаются дольше
# # # # # # # # #
# # # # # # # # #             # Получаем полностью отрендеренный HTML
# # # # # # # # #             html_content = driver.page_source
# # # # # # # # #
# # # # # # # # #             # Сохраняем HTML в файл
# # # # # # # # #             with open('page.html', 'w', encoding='utf-8') as file:
# # # # # # # # #                 file.write(html_content)
# # # # # # # # #
# # # # # # # # #             print("HTML-код сохранён в файл 'page.html'")
# # # # # # # # #
# # # # # # # # #             return html_content
# # # # # # # # #
# # # # # # # # #         except Exception as e:
# # # # # # # # #             print(f"Ошибка при загрузке страницы: {e}")
# # # # # # # # #             return None
# # # # # # # # #         finally:
# # # # # # # # #             # Обязательно закрываем драйвер
# # # # # # # # #             driver.quit()
# # # # # # # # #
# # # # # # # # #     # def fetch_page(self):
# # # # # # # # #     #     response = self.session.get(self.url, timeout=10)
# # # # # # # # #     #     response.raise_for_status()
# # # # # # # # #     #     html_content = response.text  # Сохраняем HTML в переменную
# # # # # # # # #     #     # Сохраняем HTML в файл
# # # # # # # # #     #     with open('page.html', 'w', encoding='utf-8') as file:
# # # # # # # # #     #         file.write(html_content)
# # # # # # # # #     #     print("HTML-код сохранён в файл 'page.html'")  # Опциональный вывод в консоль
# # # # # # # # #     #     # print("HTML-код страницы:")
# # # # # # # # #     #     # print(html_content)  # Выводим в консоль
# # # # # # # # #     #     return html_content  # Возвращаем строку HTML, а не BeautifulSoup
# # # # # # # # #     #     # return response.text  # Возвращаем строку HTML, а не BeautifulSoup
# # # # # # # # #     #     # return BeautifulSoup(response.content, 'html.parser')
# # # # # # # # #
# # # # # # # # #     @staticmethod
# # # # # # # # #     def parse_product_list(html_content):
# # # # # # # # #     # def parse_product_list(soup):
# # # # # # # # #         """Парсинг списка товаров на странице каталога — извлекаем URL товаров"""
# # # # # # # # #         products = []  # Инициализируем пустой список для хранения данных о товарах
# # # # # # # # #
# # # # # # # # #         # Регулярное выражение для поиска <link itemprop="url" href="...">
# # # # # # # # #         # Ищет href, начинающийся с https://goldapple.ru/
# # # # # # # # #         pattern = r'<link\s+itemprop=[""]url[""]\s+href=[""](https://goldapple.ru/\d+-\w+)[""]'
# # # # # # # # #
# # # # # # # # #         # Находим все совпадения в HTML-строке
# # # # # # # # #         matches = re.findall(pattern, html_content, re.IGNORECASE)
# # # # # # # # #
# # # # # # # # #         print("Найденные URL (регулярные выражения):")
# # # # # # # # #         print(matches)
# # # # # # # # #
# # # # # # # # #         # Формируем список товаров
# # # # # # # # #         for url in matches:
# # # # # # # # #             products.append({
# # # # # # # # #                 'url': url
# # # # # # # # #             })
# # # # # # # # #
# # # # # # # # #         print("Итоговый список товаров (products):")
# # # # # # # # #         print(products)
# # # # # # # # #
# # # # # # # # #         return products
# # # # # # # # #
# # # # # # # # #
# # # # # # # # #
# # # # # # # # #
# # # # # # # # #         # # Если ссылки на продукты лежат в тегах <link itemprop="url">
# # # # # # # # #         # product_links = soup.select('link[itemprop="url"][href^="https://goldapple.ru/"]')
# # # # # # # # #         #
# # # # # # # # #         # # Выводим итоговый список products в консоль
# # # # # # # # #         # print("Итоговый список ссылок на продукты (product_links):")
# # # # # # # # #         # print(product_links)
# # # # # # # # #         #
# # # # # # # # #         # for link in product_links:
# # # # # # # # #         #     href = link['href']  # Получаем значение href
# # # # # # # # #         #     product_url = href  # Здесь уже полный URL, префикс добавлять не нужно
# # # # # # # # #         #
# # # # # # # # #         #     # # Извлекаем название (если оно есть в атрибутах или тексте)
# # # # # # # # #         #     # name = link.get('title', 'Не указано')  # Пример — если название в title
# # # # # # # # #         #
# # # # # # # # #         #     # Далее — формируем словарь с данными о товаре, как сейчас
# # # # # # # # #         #     products.append({
# # # # # # # # #         #         'url': product_url,
# # # # # # # # #         #         # 'name': name,
# # # # # # # # #         #         # 'price': '0',  # Цена пока неизвестна — парсится на детальной странице
# # # # # # # # #         #         # 'rating': '0'  # Рейтинг пока неизвестен
# # # # # # # # #         #     })
# # # # # # # # #         #
# # # # # # # # #         # # Выводим итоговый список products в консоль
# # # # # # # # #         # print("Итоговый список товаров (products):")
# # # # # # # # #         # print(products)
# # # # # # # # #         #
# # # # # # # # #         # # cards = soup.select('a.product-card__link')  # Находим все ссылки с карточками товаров по CSS‑селектору
# # # # # # # # #         #
# # # # # # # # #         # # for card in cards:  # Перебираем каждую карточку товара в найденном списке
# # # # # # # # #         # #     # Извлекаем URL товара
# # # # # # # # #         # #     href = card.get('href')  # Получаем значение атрибута 'href' из тега <a>
# # # # # # # # #         # #     if not href:  # Проверяем, существует ли атрибут href
# # # # # # # # #         # #         continue  # Если href отсутствует, пропускаем текущую итерацию цикла — переходим к следующей карточке
# # # # # # # # #         # #
# # # # # # # # #         # #     # Формируем полный URL товара:
# # # # # # # # #         # #     # Если ссылка относительная (начинается с '/'), добавляем базовый домен
# # # # # # # # #         # #     # В противном случае используем ссылку как есть
# # # # # # # # #         # #     product_url = 'https://goldapple.ru' + href if href.startswith('/') else href
# # # # # # # # #         # #     # product_url = 'https://goldapple.ru' + card['href']
# # # # # # # # #         # #
# # # # # # # # #         # #     # Извлекаем название товара (если доступно)
# # # # # # # # #         # #     name_elem = card.select_one('span.product-card__name')  # Ищем элемент с названием товара внутри карточки
# # # # # # # # #         # #     # Если элемент найден, берём его текст и убираем лишние пробелы; иначе — ставим заглушку
# # # # # # # # #         # #     name = name_elem.text.strip() if name_elem else 'Не указано'
# # # # # # # # #         # #
# # # # # # # # #         # #     # Извлекаем цену товара (если доступна)
# # # # # # # # #         # #     price_elem = card.select_one('span.current-price')  # Ищем элемент с текущей ценой
# # # # # # # # #         # #     # Если элемент найден, удаляем все нецифровые символы из текста (оставляем только цифры цены);
# # # # # # # # #         # #     # иначе устанавливаем цену '0'
# # # # # # # # #         # #     price = re.sub(r'\D', '', price_elem.text) if price_elem else '0'
# # # # # # # # #         # #
# # # # # # # # #         # #     # Извлекаем рейтинг товара (если доступен)
# # # # # # # # #         # #     rating_elem = card.select_one('div.rating__stars')  # Ищем элемент со звездой рейтинга
# # # # # # # # #         # #     # Если элемент найден, получаем значение атрибута 'data-rating'; иначе — ставим '0'
# # # # # # # # #         # #     rating = rating_elem.get('data-rating', '0') if rating_elem else '0'
# # # # # # # # #         # #
# # # # # # # # #         # #     # name = name_elem.text.strip() if name_elem else 'Не указано'
# # # # # # # # #         # #     # price = re.sub(r'\D', '', price_elem.text) if price_elem else '0'
# # # # # # # # #         # #     # rating = rating_elem['data-rating'] if rating_elem and rating_elem.get('data-rating') else '0'
# # # # # # # # #         # #
# # # # # # # # #         # #     # Добавляем словарь с данными о текущем товаре в общий список
# # # # # # # # #         # #     products.append({
# # # # # # # # #         # #         'url': product_url,  # URL страницы товара
# # # # # # # # #         # #         'name': name,  # Название товара
# # # # # # # # #         # #         'price': price,  # Цена (только цифры)
# # # # # # # # #         # #         'rating': rating  # Рейтинг (значение из data-rating)
# # # # # # # # #         # #     })
# # # # # # # # #         # return products  # Возвращаем список словарей с информацией о всех найденных товарах
# # # # # # # # #
# # # # # # # # #     def parse_product_detail(self, soup, product_url="https://goldapple.ru/99000128231-parfumernaa-voda-love-republic-black-10ml"):
# # # # # # # # #         """Парсинг детальной информации о товаре"""
# # # # # # # # #
# # # # # # # # #         # на будущую модель
# # # # # # # # #         # soup.select_one('_ga-pdp-tabs-content_sub-title_96ko0_247').text  # артикул
# # # # # # # # #
# # # # # # # # #         # Наименование (полное)
# # # # # # # # #         name_elem = soup.select_one('_ga-pdp-tabs-content_title_96ko0_109').text  # название
# # # # # # # # #         # name_elem = soup.select_one('h1.product-main__title')
# # # # # # # # #         name = name_elem.text.strip() if name_elem else 'Не указано'
# # # # # # # # #
# # # # # # # # #         # Цена
# # # # # # # # #         price_elem = soup.select_one('span.current-price, div.price__current')
# # # # # # # # #         price = re.sub(r'\D', '', price_elem.text) if price_elem else '0'
# # # # # # # # #
# # # # # # # # #         # Описание
# # # # # # # # #         desc_elem = soup.select_one('_ga-pdp-wysiwyg_rmnt6_55[itemprop="description"]').text  # описание
# # # # # # # # #         # desc_elem = soup.select_one('div.product-description__content')
# # # # # # # # #         description = desc_elem.get_text(strip=True) if desc_elem else 'Нет описания'
# # # # # # # # #
# # # # # # # # #         # Инструкция по применению
# # # # # # # # #         instruction_header = soup.find('h3', string=re.compile(r'Способ применения', re.IGNORECASE))
# # # # # # # # #         instructions = 'Нет инструкции'
# # # # # # # # #         if instruction_header:
# # # # # # # # #             next_elem = instruction_header.find_next('div')
# # # # # # # # #             if next_elem:
# # # # # # # # #                 instructions = next_elem.get_text(strip=True)
# # # # # # # # #
# # # # # # # # #         # Страна-производитель
# # # # # # # # #         country_elem = soup.find('span', string=re.compile(r'Страна производства', re.IGNORECASE))
# # # # # # # # #         country = 'Не указано'
# # # # # # # # #         if country_elem:
# # # # # # # # #             # Ищем следующий элемент с информацией
# # # # # # # # #             country_value = country_elem.find_next('span')
# # # # # # # # #             if country_value:
# # # # # # # # #                 country = country_value.get_text(strip=True)
# # # # # # # # #
# # # # # # # # #         return Product(
# # # # # # # # #             url=product_url,
# # # # # # # # #             name=name,
# # # # # # # # #             price=price,
# # # # # # # # #             rating=self._get_rating_from_detail(soup),
# # # # # # # # #             description=description,
# # # # # # # # #             instructions=instructions,
# # # # # # # # #             country=country
# # # # # # # # #         )
# # # # # # # # #
# # # # # # # # #     @staticmethod
# # # # # # # # #     def _get_rating_from_detail(soup):
# # # # # # # # #         """Извлечение рейтинга со страницы товара"""
# # # # # # # # #         rating_elem = soup.select_one('div.rating__value')
# # # # # # # # #         if rating_elem:
# # # # # # # # #             rating_text = rating_elem.get_text()
# # # # # # # # #             match = re.search(r'\d+\.?\d*', rating_text)
# # # # # # # # #             return match.group() if match else '0'
# # # # # # # # #         return '0'
