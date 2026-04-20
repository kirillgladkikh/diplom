import os
import time
import random
import logging
from src.crawler import Crawler, check_and_get_resume_status
from src.exporter import CSVExporter
from src.parser import Parser
from src.config import OUTPUT_FILENAME, TEST_MODE, RETRY_DELAY_MIN, RETRY_DELAY_MAX, MAX_CRAWLER_ATTEMPTS


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """ПАРСИНГ САЙТА ЗОЛОТОЕ ЯБЛОКО"""
    logger.info("=" * 60)
    logger.info("ПАРСИНГ САЙТА ЗОЛОТОЕ ЯБЛОКО")
    logger.info("=" * 60)

    # Проверка наличия незавершённого краулинга
    resume = check_and_get_resume_status()

    # Шаг 1: Собираем ссылки на все продукты
    logger.info("1. Сбор ссылок на продукты...")
    crawler = Crawler()
    # Передаём параметр resume в crawler
    # - resume=True: продолжить с последней сохранённой страницы
    # - resume=False: начать сбор заново (удалив временные файлы)
    products = crawler.get_products(resume=resume)
    # # Шаг 1: Собираем ссылки на все продукты
    # logger.info("1. Сбор ссылок на продукты...")
    # crawler = Crawler()
    # # Передаём параметр resume в crawler
    # # - resume=True: продолжить с последней сохранённой страницы
    # # - resume=False: начать сбор заново (удалив временные файлы)
    # products = crawler.collect_all_links(resume=resume)
    # # # Шаг 1: Собираем ссылки на все продукты
    # # logger.info("1. Сбор ссылок на продукты...")
    # # crawler = Crawler()
    # # products = crawler.get_products(resume=resume)

    # Шаг 2: Сохраняем ссылки в CSV
    logger.info("2. Сохранение ссылок в CSV...")
    exporter = CSVExporter(OUTPUT_FILENAME)
    exporter.export(products)

    # Шаг 3: Парсим детальную информацию о продуктах
    logger.info("3. Парсинг детальной информации о продуктах...")

    # Проверяем, есть ли файл с ссылками
    csv_path = os.path.join("data", OUTPUT_FILENAME)
    if os.path.exists(csv_path):
        parser = Parser()

        if TEST_MODE:
            # В тестовом режиме парсим только первые 1 продуктов
            logger.info("Тестовый режим: парсинг первых 1 продуктов")
        else:
            # В полном режиме парсим всё
            logger.info("Полный режим: парсинг всех продуктов")
            parser.parse_all()
    else:
        logger.error(f"Файл {csv_path} не найден. Сначала запустите сбор ссылок.")

    logger.info("=" * 60)
    logger.info("ГОТОВО!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
