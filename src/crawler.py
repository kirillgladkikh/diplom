import os
import time
import random
import re
import logging
import json

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException  # НОВЫЙ: импорт для обработки таймаутов

from src.config import (
    BASE_URL, TEST_MODE, TEST_MODE_PAGES, DEFAULT_MAX_PAGES,
    REQUEST_DELAY_MIN, REQUEST_DELAY_MAX,
    PAGE_DELAY_MIN, PAGE_DELAY_MAX,  # НОВЫЙ: задержки между страницами
    RETRY_DELAY_MIN, RETRY_DELAY_MAX,  # НОВЫЙ: задержки перед повторными попытками
    RETRY_COUNT,  # ИЗМЕНЕНО: теперь используется не только для пагинации
    SELECTORS_PLP,
    CRAWLER_CHECKPOINT_FILE, CRAWLER_SAVE_EVERY_PAGES, MAX_EMPTY_PAGES
)
from src.product import Product

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Crawler:
    """Обход страниц и сбор ссылок на продукты"""
    def __init__(self):
        self.base_url = BASE_URL
        self.product_links = set()
        self.driver = None
        self.last_processed_page = 0  # НОВОЕ: для отслеживания прогресса

    def _init_driver(self):
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

    def _save_checkpoint(self, current_page):
        """Сохраняет номер обработанной страницы и все собранные ссылки"""
        checkpoint = {
            "last_page": current_page,  # ← номер страницы, которую ТОЛЬКО ЧТО ОБРАБОТАЛИ
            "total_links": len(self.product_links),
            "links": list(self.product_links)
        }
        try:
            with open(CRAWLER_CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
                json.dump(checkpoint, f, ensure_ascii=False, indent=2)
            logger.info(f"Чекпоинт: страница {current_page}, собрано {len(self.product_links)} ссылок")
        except Exception as e:
            logger.warning(f"Не удалось сохранить чекпоинт: {e}")

    def _load_checkpoint(self):
        """Загружает прогресс и возвращает номер последней ОБРАБОТАННОЙ страницы"""
        if not os.path.exists(CRAWLER_CHECKPOINT_FILE):
            return 0

        try:
            with open(CRAWLER_CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)

            self.product_links = set(checkpoint.get("links", []))
            last_page = checkpoint.get("last_page", 0)

            logger.info(
                f"Загружен чекпоинт: обработана страница {last_page}, собрано {len(self.product_links)} ссылок")
            return last_page  # ← возвращаем номер ОБРАБОТАННОЙ страницы
        except Exception as e:
            logger.warning(f"Не удалось загрузить чекпоинт: {e}")
            return 0

    def _clear_checkpoint(self):
        """Удаляет файл чекпоинта после успешного завершения"""
        try:
            if os.path.exists(CRAWLER_CHECKPOINT_FILE):
                os.remove(CRAWLER_CHECKPOINT_FILE)
                logger.info("🗑️ Чекпоинт удалён (краулинг завершён)")
        except Exception as e:
            logger.warning(f"Не удалось удалить чекпоинт: {e}")

    def _random_delay(self, min_delay=None, max_delay=None):
        """Случайная задержка"""
        # ИЗМЕНЕНО: теперь можно переопределять диапазон задержки
        min_d = min_delay if min_delay is not None else REQUEST_DELAY_MIN
        max_d = max_delay if max_delay is not None else REQUEST_DELAY_MAX
        delay = random.uniform(min_d, max_d)
        time.sleep(delay)
    # def _random_delay(self):
    #     """Случайная задержка"""
    #     delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
    #     time.sleep(delay)

    # def _get_total_pages(self):
    #     """Определяет общее количество страниц"""
    #     if TEST_MODE:
    #         logger.info(f"Тестовый режим: обрабатываем {TEST_MODE_PAGES} страниц")
    #         return TEST_MODE_PAGES
    #
    #     # НОВЫЙ: цикл повторных попыток при определении количества страниц
    #     for attempt in range(RETRY_COUNT):
    #         try:
    #             self.driver.get(self.base_url)
    #             self._random_delay()
    #
    #             # НОВЫЙ: явное ожидание загрузки пагинации
    #             WebDriverWait(self.driver, 10).until(
    #                 EC.presence_of_element_located((By.CSS_SELECTOR, SELECTORS_PLP["pagination_container"]))
    #             )
    #
    #             pagination = self.driver.find_element(By.CSS_SELECTOR, SELECTORS_PLP["pagination_container"])
    #             pagination_text = pagination.text
    #             numbers = re.findall(r'\d+', pagination_text)
    #             if numbers:
    #                 last_page = max(int(n) for n in numbers)
    #                 logger.info(f"Всего страниц: {last_page}")
    #                 return min(last_page, DEFAULT_MAX_PAGES)
    #
    #         # НОВЫЙ: обработка таймаута
    #         except TimeoutException:
    #             logger.warning(f"Таймаут при определении количества страниц, попытка {attempt + 1}/{RETRY_COUNT}")
    #             if attempt < RETRY_COUNT - 1:
    #                 self._random_delay(RETRY_DELAY_MIN, RETRY_DELAY_MAX)
    #
    #         except Exception as e:
    #             logger.error(f"Не удалось определить количество страниц: {e}")
    #             if attempt < RETRY_COUNT - 1:
    #                 self._random_delay(RETRY_DELAY_MIN, RETRY_DELAY_MAX)
    #
    #     # ИЗМЕНЕНО: логирование при использовании значения по умолчанию
    #     logger.warning(f"Не удалось определить количество страниц, используем DEFAULT_MAX_PAGES={DEFAULT_MAX_PAGES}")
    #     return DEFAULT_MAX_PAGES
    # # def _get_total_pages(self):
    # #     """Определяет общее количество страниц"""
    # #     if TEST_MODE:
    # #         # Тестовый режим
    # #         logger.info(f"Тестовый режим: обрабатываем {TEST_MODE_PAGES} страниц")
    # #         return TEST_MODE_PAGES
    # #
    # #     try:
    # #         # Боевой режим
    # #         self.driver.get(self.base_url)
    # #         self._random_delay()  # ← используем случайную задержку
    # #
    # #         pagination = self.driver.find_element(By.CSS_SELECTOR, SELECTORS_PLP["pagination_container"])
    # #         pagination_text = pagination.text
    # #         numbers = re.findall(r'\d+', pagination_text)
    # #         if numbers:
    # #             last_page = max(int(n) for n in numbers)
    # #             logger.info(f"Всего страниц: {last_page}")
    # #             return min(last_page, DEFAULT_MAX_PAGES)
    # #     except Exception as e:
    # #         logger.error(f"Не удалось определить количество страниц: {e}")
    # #
    # #     return DEFAULT_MAX_PAGES

    def _extract_links_from_page(self, page_num):
        """Извлекает ссылки на продукты с одной страницы"""
        url = f"{self.base_url}?p={page_num}"
        logger.info(f"Страница {page_num}: {url}")

        # НОВЫЙ: цикл повторных попыток для загрузки страницы
        for attempt in range(RETRY_COUNT):
            try:
                self.driver.get(url)
                self._random_delay()

                # НОВЫЙ: явное ожидание загрузки тела страницы
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                page_links = []
                pattern = SELECTORS_PLP["product_link_pattern"]

                all_links = self.driver.find_elements(By.TAG_NAME, "a")

                for link in all_links:
                    try:
                        href = link.get_attribute('href')
                        if not href:
                            continue

                        clean_href = href.split('?')[0]

                        if re.search(pattern, clean_href):
                            if clean_href not in self.product_links:
                                page_links.append(clean_href)
                                self.product_links.add(clean_href)
                    except:
                        continue

                logger.info(f"Найдено {len(page_links)} новых ссылок")
                return len(page_links)

            # НОВЫЙ: обработка таймаута
            except TimeoutException:
                logger.warning(f"Таймаут на странице {page_num}, попытка {attempt + 1}/{RETRY_COUNT}")
                if attempt < RETRY_COUNT - 1:
                    self._random_delay(RETRY_DELAY_MIN, RETRY_DELAY_MAX)

            except Exception as e:
                logger.error(f"Ошибка на странице {page_num}: {e}")
                if attempt < RETRY_COUNT - 1:
                    self._random_delay(RETRY_DELAY_MIN, RETRY_DELAY_MAX)
                else:
                    return 0
        return 0
    # def _extract_links_from_page(self, page_num):
    #     """Извлекает ссылки на продукты с одной страницы"""
    #     url = f"{self.base_url}?p={page_num}"
    #     logger.info(f"Страница {page_num}: {url}")
    #
    #     try:
    #         self.driver.get(url)
    #         self._random_delay()  # ← используем случайную задержку
    #
    #         page_links = []
    #         pattern = SELECTORS_PLP["product_link_pattern"]
    #
    #         # Находим все ссылки на странице
    #         all_links = self.driver.find_elements(By.TAG_NAME, "a")
    #
    #         for link in all_links:
    #             try:
    #                 href = link.get_attribute('href')
    #                 if not href:
    #                     continue
    #
    #                 # Очищаем от параметров
    #                 clean_href = href.split('?')[0]
    #
    #                 # Проверяем структуру URL
    #                 if re.search(pattern, clean_href):
    #                     if clean_href not in self.product_links:
    #                         page_links.append(clean_href)
    #                         self.product_links.add(clean_href)
    #             except:
    #                 continue
    #
    #         logger.info(f"Найдено {len(page_links)} новых ссылок")
    #         return len(page_links)
    #
    #     except Exception as e:
    #         logger.error(f"Ошибка на странице {page_num}: {e}")
    #         return 0

    def _check_empty_page(self, page_num, links_found):
        """Проверяет, не достигли ли мы конца каталога"""
        # Если на странице 0 ссылок - возможно, это конец
        if links_found == 0 and page_num > 1:
            logger.warning(f"На странице {page_num} найдено 0 ссылок. Возможно, достигнут конец каталога.")
            return True
        return False

    def collect_all_links(self, resume=True):
        """Собирает все ссылки на продукты с возможностью возобновления после прерывания"""
        self.driver = self._init_driver()
        products = []

        # Счётчик пустых страниц подряд
        consecutive_empty_pages = 0

        try:
            # Определяем максимальное количество страниц (из конфига)
            total_pages = DEFAULT_MAX_PAGES
            logger.info(f"Максимальное количество страниц для обхода: {total_pages}")

            # Загружаем сохранённый прогресс
            start_page = 1
            if resume:
                last_processed_page = self._load_checkpoint()
                if last_processed_page > 0:
                    if last_processed_page >= total_pages:
                        logger.info("Все страницы уже обработаны")
                        for link in self.product_links:
                            products.append(Product(url=link))
                        return products
                    start_page = last_processed_page + 1
                    logger.info(
                        f"Возобновляем со страницы {start_page} (последняя обработанная: {last_processed_page})")

            logger.info(f"Начинаем сбор со страницы {start_page} из {total_pages}")

            for page in range(start_page, total_pages + 1):
                # Получаем количество ссылок на странице
                links_found = self._extract_links_from_page(page)

                # Проверка: если страница пустая
                if links_found == 0:
                    consecutive_empty_pages += 1
                    logger.warning(f"Страница {page}: 0 ссылок (пустых страниц подряд: {consecutive_empty_pages})")

                    # Останавливаемся после MAX_EMPTY_PAGES пустых страниц
                    if consecutive_empty_pages >= MAX_EMPTY_PAGES:
                        logger.warning(f"Достигнут конец каталога - {consecutive_empty_pages} пустых страниц подряд")
                        break
                else:
                    # Сбрасываем счётчик если нашли ссылки
                    consecutive_empty_pages = 0

                self.last_processed_page = page

                # Сохраняем чекпоинт
                self._save_checkpoint(page)

                # Задержка между страницами
                if page < total_pages and not TEST_MODE:
                    logger.info(f"Ожидание перед загрузкой следующей страницы...")
                    self._random_delay(PAGE_DELAY_MIN, PAGE_DELAY_MAX)

                if TEST_MODE and page >= TEST_MODE_PAGES:
                    break

            # Успешно завершили - удаляем чекпоинт
            self._clear_checkpoint()

            for link in self.product_links:
                products.append(Product(url=link))

            logger.info(f"Сбор завершён! Всего собрано {len(products)} ссылок")
            return products

        except KeyboardInterrupt:
            logger.warning("Прерывание пользователем! Прогресс сохранён")
            for link in self.product_links:
                products.append(Product(url=link))
            return products

        except Exception as e:
            logger.error(f"Критическая ошибка: {e}")
            if hasattr(self, 'last_processed_page') and self.last_processed_page > 0:
                self._save_checkpoint(self.last_processed_page)
            for link in self.product_links:
                products.append(Product(url=link))
            return products

        finally:
            if self.driver:
                self.driver.quit()
    # def collect_all_links(self, resume=True):
    #     """Собирает все ссылки на продукты с возможностью возобновления после прерывания"""
    #     self.driver = self._init_driver()
    #     products = []
    #
    #     # Счётчик пустых страниц подряд (для обнаружения конца каталога)
    #     consecutive_empty_pages = 0
    #
    #     try:
    #         total_pages = self._get_total_pages()
    #
    #         # Загружаем сохранённый прогресс
    #         start_page = 1
    #         if resume:
    #             last_processed_page = self._load_checkpoint()  # возвращает номер последней ОБРАБОТАННОЙ страницы
    #             if last_processed_page > 0:
    #                 if last_processed_page >= total_pages:
    #                     logger.info("Все страницы уже обработаны")
    #                     for link in self.product_links:
    #                         products.append(Product(url=link))
    #                     return products
    #                 start_page = last_processed_page + 1  # начинаем СО СЛЕДУЮЩЕЙ страницы
    #                 logger.info(
    #                     f"Возобновляем со страницы {start_page} (последняя обработанная: {last_processed_page})")
    #
    #         logger.info(f"Начинаем сбор со страницы {start_page} из {total_pages}")
    #
    #         for page in range(start_page, total_pages + 1):
    #             # Получаем количество ссылок на странице
    #             links_found = self._extract_links_from_page(page)
    #
    #             # НОВАЯ ПРОВЕРКА: обнаружение конца каталога (3 пустые страницы подряд)
    #             if links_found == 0:
    #                 consecutive_empty_pages += 1
    #                 logger.warning(
    #                     f"Страница {page}: найдено 0 ссылок (пустых страниц подряд: {consecutive_empty_pages})")
    #
    #                 if consecutive_empty_pages >= MAX_EMPTY_PAGES:
    #                     logger.warning(
    #                         f"{consecutive_empty_pages} страниц подряд без ссылок. "
    #                         f"Достигнут конец каталога. Останавливаем краулинг.")
    #                     break
    #             else:
    #                 # Сброс счётчика если нашли ссылки
    #                 consecutive_empty_pages = 0
    #
    #             self.last_processed_page = page
    #
    #             # Сохраняем чекпоинт ПОСЛЕ КАЖДОЙ страницы (надёжнее)
    #             self._save_checkpoint(page)
    #
    #             # Задержка между страницами
    #             if page < total_pages and not TEST_MODE:
    #                 logger.info(f"Ожидание перед загрузкой следующей страницы...")
    #                 self._random_delay(PAGE_DELAY_MIN, PAGE_DELAY_MAX)
    #
    #             if TEST_MODE and page >= TEST_MODE_PAGES:
    #                 break
    #
    #         # Успешно завершили - удаляем чекпоинт
    #         self._clear_checkpoint()
    #
    #         for link in self.product_links:
    #             products.append(Product(url=link))
    #
    #         logger.info(f"Сбор завершён! Всего собрано {len(products)} ссылок")
    #         return products
    #
    #     except KeyboardInterrupt:
    #         logger.warning("Прерывание пользователем! Прогресс сохранён")
    #         # Чекпоинт уже сохранился после каждой страницы, просто возвращаем что собрали
    #         for link in self.product_links:
    #             products.append(Product(url=link))
    #         return products
    #
    #     except Exception as e:
    #         logger.error(f"Критическая ошибка: {e}")
    #         # Сохраняем прогресс перед выходом
    #         if hasattr(self, 'last_processed_page') and self.last_processed_page > 0:
    #             self._save_checkpoint(self.last_processed_page)
    #         for link in self.product_links:
    #             products.append(Product(url=link))
    #         return products
    #
    #     finally:
    #         if self.driver:
    #             self.driver.quit()
    # # def collect_all_links(self):
    # #     """Собирает все ссылки на продукты"""
    # #     self.driver = self._init_driver()
    # #     products = []
    # #
    # #     try:
    # #         total_pages = self._get_total_pages()
    # #
    # #         for page in range(1, total_pages + 1):
    # #             self._extract_links_from_page(page)
    # #
    # #             # НОВЫЙ: задержка между страницами (важно для вежливого поведения)
    # #             if page < total_pages and not TEST_MODE:
    # #                 logger.info(f"Ожидание перед загрузкой следующей страницы...")
    # #                 self._random_delay(PAGE_DELAY_MIN, PAGE_DELAY_MAX)
    # #
    # #             if TEST_MODE and page >= TEST_MODE_PAGES:
    # #                 break
    # #
    # #         for link in self.product_links:
    # #             products.append(Product(url=link))
    # #
    # #         logger.info(f"Сбор завершён! Всего собрано {len(products)} ссылок")
    # #         return products
    # #
    # #     finally:
    # #         if self.driver:
    # #             self.driver.quit()
    # # # def collect_all_links(self):
    # # #     """Собирает все ссылки на продукты"""
    # # #     self.driver = self._init_driver()
    # # #     products = []
    # # #
    # # #     try:
    # # #         total_pages = self._get_total_pages()
    # # #
    # # #         for page in range(1, total_pages + 1):
    # # #             self._extract_links_from_page(page)
    # # #
    # # #             if TEST_MODE and page >= TEST_MODE_PAGES:
    # # #                 break
    # # #
    # # #         # Создаём объекты Product из ссылок
    # # #         for link in self.product_links:
    # # #             products.append(Product(url=link))
    # # #
    # # #         logger.info(f"Сбор завершён! Всего собрано {len(products)} ссылок")
    # # #         return products
    # # #
    # # #     finally:
    # # #         if self.driver:
    # # #             self.driver.quit()

    def get_products(self, resume=True):
        """Главный метод для получения продуктов"""
        return self.collect_all_links(resume=resume)


def check_and_get_resume_status():
    """
    Проверяет наличие незавершённого краулинга и спрашивает пользователя
    Функция check_and_get_resume_status():
     - Проверяет, есть ли временные файлы (crawler_temp_links.txt, crawler_checkpoint.json)
     - Если есть - спрашивает пользователя: возобновить или начать заново
     - Возвращает True (возобновить) или False (начать заново)
    """
    temp_file = "crawler_temp_links.txt"
    checkpoint_file = "crawler_checkpoint.json"

    if os.path.exists(temp_file) or os.path.exists(checkpoint_file):
        logger.warning("Обнаружен незавершённый краулинг!")
        response = input("Возобновить с последнего сохранённого места? (y/n): ").lower()
        resume = response == 'y'

        if not resume:
            # Удаляем временные файлы
            for f in [temp_file, checkpoint_file]:
                if os.path.exists(f):
                    os.remove(f)
                    logger.info(f"Удалён {f}")
        return resume
    else:
        return True


# РАБОТАЕТ !!!
# from src.parser import Parser
# # from urllib.parse import urljoin
# import time
# import random
# import logging
#
#
# # Настройка логирования
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('scraper.log', encoding='utf-8'),
#         logging.StreamHandler()
#     ]
# )
# logger = logging.getLogger(__name__)
#
#
# class Crawler:
#     def __init__(self, base_url, delay=2, test_mode=True):
#         self.base_url = base_url
#         self.delay = delay
#         self.test_mode = test_mode  # Берётся из TEST_MODE
#         # self.parser = Parser(base_url)
#
#     # def get_product_urls(self, page_url):
#     #     soup = self.parser.fetch_page()
#     #     product_links = []
#     #     for link in soup.select('a.product-card__link'):
#     #         href = link['href']
#     #         full_url = urljoin(self.base_url, href)
#     #         product_links.append(full_url)
#     #     return product_links
#
#     def _detect_total_pages(self, soup):
#         """Автоматическое определение общего количества страниц"""
#         try:
#             # Пробуем разные селекторы для пагинации
#             pagination = (
#                     soup.select_one('div.pagination') or
#                     soup.select_one('.pagination') or
#                     soup.select_one('[data-pagination]') or
#                     soup.select_one('.page-nav')
#             )
#             # # Ищем элемент с пагинацией
#             # pagination = soup.select_one('div.pagination')
#             if not pagination:
#                 return 1  # Если пагинации нет — одна страница
#
#             # Пробуем разные селекторы для пагинации
#             page_links = (
#                     pagination.select('a.pagination__link') or
#                     pagination.select('a[href*="page="]') or
#                     pagination.select('.page-number')
#             )
#             # # Ищем все номера страниц
#             # page_links = pagination.select('a.pagination__link')
#             if not page_links:
#                 return 1
#
#             # Считаем, что последний номер страницы = 1.
#             # Это «страховка»: если не найдём номеров страниц или все попытки парсинга провалятся,
#             # программа будет считать, что есть хотя бы одна страница.
#             last_page_num = 1
#             for link in page_links:
#                 try:
#                     page_num = int(link.text.strip())
#                     if page_num > last_page_num:
#                         last_page_num = page_num
#                 except ValueError:
#                     continue
#             return last_page_num
#         except Exception as e:
#             logger.warning(f"Не удалось определить количество страниц: {e}")
#             return 3 if self.test_mode else 10  # В тестовом режиме — 3 страницы, иначе — 10
#             # return 10  # По умолчанию — 10 страниц
#
#     def crawl(self, max_pages=3):
#         all_products = []
#         page_num = 1
#
#         while True:
#         # for page_num in range(1, max_pages + 1):
#             page_url = f"{self.base_url}?page={page_num}"
#             logger.info(f"Парсинг страницы {page_num}: {page_url}")
#             print(f"Парсинг страницы {page_num}: {page_url}")
#
#             try:
#                 # --- НАЧАЛО РЕАЛИЗАЦИИ ПРОЦЕССА НАВИГАЦИИ ---
#
#                 # 1. Создаём отдельный парсер для текущей страницы каталога
#                 #    Это позволяет получить доступ к содержимому страницы с товарами
#                 catalog_parser = Parser(page_url)
#                 # Парсим список товаров на странице
#                 soup = catalog_parser.fetch_page()
#
#                 logger.debug(f"Загружено HTML (первые 500 символов): {str(soup)[:500]}")
#                 logger.info(f"Проверка пагинации: ищем селекторы...")
#                 pagination_debug = soup.select('div.pagination, .pagination')
#                 logger.info(f"Найдено блоков пагинации: {len(pagination_debug)}")
#                 if pagination_debug:
#                     page_links_debug = pagination_debug[0].select('a')
#                     logger.info(f"Найдено ссылок в пагинации: {len(page_links_debug)}")
#                     for i, link in enumerate(page_links_debug[:5]):
#                         logger.debug(
#                             f"Ссылка пагинации {i}: {link.get('href', 'нет href')} текст: {link.get_text(strip=True)}")
#
#                 # Автоматическое определение количества страниц
#                 if max_pages is None:
#                     max_pages = self._detect_total_pages(soup)
#                     logger.info(f"Обнаружено страниц: {max_pages}")
#
#                 # В тестовом режиме ограничиваем количество страниц
#                 if self.test_mode and max_pages > 3:
#                     max_pages = 3
#                     logger.info("Активирован тестовый режим — парсинг ограничен 3 страницами")
#
#                 # 2. Получаем список товаров с текущей страницы каталога
#                 #    Используем метод parse_product_list для извлечения базовой информации
#                 #    (URL, название, цена, рейтинг) о каждом товаре на странице
#                 html_content = catalog_parser.fetch_page()
#                 product_list = catalog_parser.parse_product_list(html_content)
#                 # product_list = catalog_parser.parse_product_list(soup)
#
#                 if not product_list:  # Если на странице нет товаров — проверяем следующую страницу...
#                     logger.warning(f"На странице {page_num} не найдено товаров. Проверяем следующую страницу...")
#                     if page_num >= max_pages:
#                         break
#                     page_num += 1
#                     time.sleep(random.uniform(3, 5))
#                     continue
#                     # logger.info("Достигнут конец пагинации")
#                     # break
#
#                 logger.info(f"Найдено товаров на странице: {len(product_list)}")
#
#                 # 3. Для каждого товара из списка:
#                 #    а) создаём новый парсер для страницы конкретного товара;
#                 #    б) переходим на страницу товара по извлечённому URL;
#                 #    в) парсим детальную информацию о товаре
#                 for product_info in product_list:
#                     try:
#                         # Создаём парсер для страницы конкретного товара
#                         detail_parser = Parser(product_info['url'])
#                         # Загружаем содержимое страницы товара
#                         detail_soup = detail_parser.fetch_page()
#                         # Парсим детальную информацию (описание, инструкция, страна и т.д.)
#                         product = detail_parser.parse_product_detail(detail_soup, product_info['url'])
#
#                         # Обновляем данные из каталога, если нужно (например, если на детальной странице нет цены)
#                         if product.price == '0':
#                             product.price = product_info['price']
#                         if product.rating == '0':
#                             product.rating = product_info['rating']
#
#                         all_products.append(product)
#                         logger.info(f"Обработан товар: {product.name}")
#
#                         # Случайная задержка между запросами (2–4 секунды)
#                         sleep_time = random.uniform(2, 4)
#                         time.sleep(sleep_time)  # Задержка для избежания блокировки
#
#                     except Exception as e:
#                         logger.error(f"Ошибка при обработке товара {product_info.get('url', 'unknown')}: {e}")
#                         continue
#
#             # --- КОНЕЦ РЕАЛИЗАЦИИ ПРОЦЕССА НАВИГАЦИИ ---
#
#             except Exception as e:
#                 logger.error(f"Ошибка при обработке страницы {page_url}: {e}")
#                 break  # или continue, в зависимости от логики
#
#             # Проверка условия завершения (достигнут ли лимит страниц)
#             if max_pages and page_num >= max_pages:
#                 break
#
#             page_num += 1
#
#             # Дополнительная задержка между страницами
#             time.sleep(random.uniform(3, 5))
#
#         return all_products
