from src.crawler import Crawler
from src.exporter import CSVExporter
import logging
import sys


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

# Флаг тестового режима
TEST_MODE = True  # Установите False для полного парсинга

BASE_URL = "https://goldapple.ru/parfjumerija"
OUTPUT_FILE = "output/goldapple_perfumes.csv"

# использованы АКУТАЛЬНЫЕ селекторы полей
def main():
    logger.info("Запуск скрапинга Gold Apple Парфюмерия")

    # Инициализация краулера (задержка 2 секунды между запросами)
    crawler = Crawler(BASE_URL, delay=2)
    # products = crawler.crawl(max_pages=3)  # Сканирование 3 страниц для теста

    try:
        products = crawler.crawl()  # Автоматическое определение страниц
        logger.info(f"Собрано товаров: {len(products)}")

        # Экспорт в CSV
        exporter = CSVExporter(OUTPUT_FILE)
        exporter.export(products)

        logger.info(f"Данные успешно сохранены в {OUTPUT_FILE}")

    except Exception as e:
        logger.critical(f"Критическая ошибка при выполнении скрапинга: {e}")

if __name__ == "__main__":
    main()


# def main():
#     BASE_URL = "https://goldapple.ru/parfjumerija"
#     logger.info(f"Проверяем формат URL товаров на {BASE_URL}")
#
#     # Быстрая проверка: берём первую страницу, парсим 1–2 товара
#     test_crawler = Crawler(BASE_URL, delay=2, test_mode=True)
#     test_products = test_crawler.crawl(max_pages=1)  # Только 1 страница
#
#     if test_products:
#         sample_url = test_products[0].url
#         logger.info(f"Образец URL товара: {sample_url}")
#         if '/catalog/product/view/' in sample_url:
#             logger.critical("Формат URL запрещён robots.txt. Прекращаем парсинг.")
#             return
#         else:
#             logger.info("Формат URL безопасен. Запускаем полный парсинг...")
#             # Запускаем основной парсинг
#             full_crawler = Crawler(BASE_URL, delay=2, test_mode=False)
#             products = full_crawler.crawl()
#             # Экспорт и т. д.
#     else:
#         logger.error("Не удалось получить тестовые данные. Проверьте подключение.")
