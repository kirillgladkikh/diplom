from src.crawler import Crawler
from src.exporter import CSVExporter
from src.config import OUTPUT_FILENAME


def main():
    """Главный модуль для запуска парсера"""
    print("\n" + "=" * 60)
    print("ПАРСИНГ САЙТА ЗОЛОТОЕ ЯБЛОКО")
    print("=" * 60 + "\n")

    # Шаг 1: Собираем ссылки на все продукты
    print("1. Сбор ссылок на продукты...")
    crawler = Crawler()
    products = crawler.get_products()

    # Шаг 2: Сохраняем в CSV
    print("\n2. Сохранение результатов...")
    exporter = CSVExporter(OUTPUT_FILENAME)
    exporter.export(products)

    print("\n" + "=" * 60)
    print("ГОТОВО!")
    print(f"Собрано ссылок: {len(products)}")
    print("=" * 60)


if __name__ == "__main__":
    main()





# from src.crawler import Crawler
# from src.exporter import CSVExporter
# import logging
# import sys
# from src.parser import Parser
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
# # Флаг тестового режима
# TEST_MODE = True  # Установите False для полного парсинга
#
# BASE_URL = "https://goldapple.ru/parfjumerija"
# OUTPUT_FILE = "output/goldapple_perfumes.csv"
#
# # использованы АКУТАЛЬНЫЕ селекторы полей
# def main():
#     """Запуск тестового режима (3 страницы)"""
#     print("\n" + "=" * 60)
#     print("🧪 ТЕСТОВЫЙ РЕЖИМ: сбор ссылок с первых 3 страниц")
#     print("=" * 60 + "\n")
#
#     parser = Parser("https://goldapple.ru/parfjumerija", test_mode=True)
#     parser.save_to_csv("goldapple_perfumes_test.csv")
#
#     print("\n" + "=" * 60)
#     print("✅ Тестовый режим завершён!")
#     print("📁 Результат сохранён в файл: goldapple_perfumes_test.csv")
#     print("=" * 60)
#
#     # # Базовый сборщик — только ссылки
#     # parser = Parser("https://goldapple.ru/parfjumerija")
#     # parser.save_to_csv("goldapple_perfumes.csv")
#
#     # # Использование
#     # parser = Parser("https://goldapple.ru/parfjumerija")
#     # product_url = parser.find_product_url()
#     # print(product_url)
#
#     # # Инициализация парсера
#     # parser = Parser(url=BASE_URL)
#     # parser.fetch_page()
#
#
# #     logger.info("Запуск скрапинга Gold Apple Парфюмерия")
# #
# #     # Инициализация краулера (задержка 2 секунды между запросами)
# #     crawler = Crawler(
# #         base_url=BASE_URL,
# #         delay=2,
# #         test_mode=TEST_MODE  # Передаём значение глобальной переменной
# #     )
# #
# #     # products = crawler.crawl(max_pages=3)  # Сканирование 3 страниц для теста
# #     try:
# #         products = crawler.crawl(max_pages=None)  # Запускаем автоопределение
# #         logger.info(f"Собрано товаров: {len(products)}")
# #
# #         # Экспорт в CSV
# #         exporter = CSVExporter(OUTPUT_FILE)
# #         exporter.export(products)
# #
# #         logger.info(f"Данные успешно сохранены в {OUTPUT_FILE}")
# #
# #     except Exception as e:
# #         logger.critical(f"Критическая ошибка при выполнении скрапинга: {e}")
#
# if __name__ == "__main__":
#     main()
