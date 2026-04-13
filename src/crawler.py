from src.parser import Parser
# from urllib.parse import urljoin
import time
import random
import logging


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Crawler:
    def __init__(self, base_url, delay=2, test_mode=True):
        self.base_url = base_url
        self.delay = delay
        self.test_mode = test_mode
        # self.parser = Parser(base_url)

    # def get_product_urls(self, page_url):
    #     soup = self.parser.fetch_page()
    #     product_links = []
    #     for link in soup.select('a.product-card__link'):
    #         href = link['href']
    #         full_url = urljoin(self.base_url, href)
    #         product_links.append(full_url)
    #     return product_links

    def _detect_total_pages(self, soup):
        """Автоматическое определение общего количества страниц"""
        try:
            # Ищем элемент с пагинацией
            pagination = soup.select_one('div.pagination')
            if not pagination:
                return 1  # Если пагинации нет — одна страница

            # Ищем все номера страниц
            page_links = pagination.select('a.pagination__link')
            if not page_links:
                return 1

            # Считаем, что последний номер страницы = 1.
            # Это «страховка»: если не найдём номеров страниц или все попытки парсинга провалятся,
            # программа будет считать, что есть хотя бы одна страница.
            last_page_num = 1
            for link in page_links:
                try:
                    page_num = int(link.text.strip())
                    if page_num > last_page_num:
                        last_page_num = page_num
                except ValueError:
                    continue
            return last_page_num
        except Exception as e:
            logger.warning(f"Не удалось определить количество страниц: {e}")
            return 3 if self.test_mode else 10  # В тестовом режиме — 3 страницы, иначе — 10
            # return 10  # По умолчанию — 10 страниц

    def crawl(self, max_pages=3):
        all_products = []
        page_num = 1

        while True:
        # for page_num in range(1, max_pages + 1):
            page_url = f"{self.base_url}?page={page_num}"
            logger.info(f"Парсинг страницы {page_num}: {page_url}")
            print(f"Парсинг страницы {page_num}: {page_url}")

            try:
                # --- НАЧАЛО РЕАЛИЗАЦИИ ПРОЦЕССА НАВИГАЦИИ ---

                # 1. Создаём отдельный парсер для текущей страницы каталога
                #    Это позволяет получить доступ к содержимому страницы с товарами
                catalog_parser = Parser(page_url)
                # -----Парсим список товаров на странице
                soup = self.parser.fetch_page()

                # -----Автоматическое определение количества страниц
                if max_pages is None:
                    max_pages = self._detect_total_pages(soup)
                    logger.info(f"Обнаружено страниц: {max_pages}")

                # -----В тестовом режиме ограничиваем количество страниц
                if self.test_mode and max_pages > 3:
                    max_pages = 3
                    logger.info("Активирован тестовый режим — парсинг ограничен 3 страницами")

                # 2. Получаем список товаров с текущей страницы каталога
                #    Используем метод parse_product_list для извлечения базовой информации
                #    (URL, название, цена, рейтинг) о каждом товаре на странице
                product_list = catalog_parser.parse_product_list(soup)

                if not product_list:  # Если на странице нет товаров — конец пагинации
                    logger.info("Достигнут конец пагинации")
                    break

                logger.info(f"Найдено товаров на странице: {len(product_list)}")

                # 3. Для каждого товара из списка:
                #    а) создаём новый парсер для страницы конкретного товара;
                #    б) переходим на страницу товара по извлечённому URL;
                #    в) парсим детальную информацию о товаре
                for product_info in product_list:
                    try:
                        # Создаём парсер для страницы конкретного товара
                        detail_parser = Parser(product_info['url'])
                        # Загружаем содержимое страницы товара
                        detail_soup = detail_parser.fetch_page()
                        # Парсим детальную информацию (описание, инструкция, страна и т.д.)
                        product = detail_parser.parse_product_detail(detail_soup, product_info['url'])

                        # Обновляем данные из каталога, если нужно (например, если на детальной странице нет цены)
                        if product.price == '0':
                            product.price = product_info['price']
                        if product.rating == '0':
                            product.rating = product_info['rating']

                        all_products.append(product)
                        logger.info(f"Обработан товар: {product.name}")

                        # Случайная задержка между запросами (2–4 секунды)
                        sleep_time = random.uniform(2, 4)
                        time.sleep(sleep_time)  # Задержка для избежания блокировки

                    except Exception as e:
                        logger.error(f"Ошибка при обработке товара {product_info.get('url', 'unknown')}: {e}")
                        continue

            # --- КОНЕЦ РЕАЛИЗАЦИИ ПРОЦЕССА НАВИГАЦИИ ---

            except Exception as e:
                logger.error(f"Ошибка при обработке страницы {page_url}: {e}")
                break  # или continue, в зависимости от логики

            # Проверка условия завершения (достигнут ли лимит страниц)
            if max_pages and page_num >= max_pages:
                break

            page_num += 1

            # Дополнительная задержка между страницами
            time.sleep(random.uniform(3, 5))

        return all_products
