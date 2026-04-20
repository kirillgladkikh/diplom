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
from selenium.common.exceptions import TimeoutException

from src.config import (
    BASE_URL, TEST_MODE, TEST_MODE_PAGES, DEFAULT_MAX_PAGES,
    REQUEST_DELAY_MIN, REQUEST_DELAY_MAX,
    PAGE_DELAY_MIN, PAGE_DELAY_MAX,
    RETRY_DELAY_MIN, RETRY_DELAY_MAX,
    RETRY_COUNT,
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

    def _extract_links_from_page(self, page_num):
        """Извлекает ссылки на продукты с одной страницы"""
        url = f"{self.base_url}?p={page_num}"
        logger.info(f"Страница {page_num}: {url}")

        # Цикл повторных попыток для загрузки страницы
        for attempt in range(RETRY_COUNT):
            try:
                self.driver.get(url)
                self._random_delay()

                # Явное ожидание загрузки тела страницы
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

            # Обработка таймаута
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
