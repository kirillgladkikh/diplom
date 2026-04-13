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
    crawler = Crawler(
        base_url=BASE_URL,
        delay=2,
        test_mode=TEST_MODE  # Передаём значение глобальной переменной
    )

    # products = crawler.crawl(max_pages=3)  # Сканирование 3 страниц для теста
    try:
        products = crawler.crawl(max_pages=None)  # Запускаем автоопределение
        logger.info(f"Собрано товаров: {len(products)}")

        # Экспорт в CSV
        exporter = CSVExporter(OUTPUT_FILE)
        exporter.export(products)

        logger.info(f"Данные успешно сохранены в {OUTPUT_FILE}")

    except Exception as e:
        logger.critical(f"Критическая ошибка при выполнении скрапинга: {e}")

if __name__ == "__main__":
    main()
