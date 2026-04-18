import os
import time
import random
import logging
from src.crawler import Crawler
from src.exporter import CSVExporter
from src.parser import Parser
from src.config import OUTPUT_FILENAME, TEST_MODE, RETRY_DELAY_MIN, RETRY_DELAY_MAX, MAX_CRAWLER_ATTEMPTS


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Главный модуль для запуска парсера"""
    logger.info("=" * 60)
    logger.info("ПАРСИНГ САЙТА ЗОЛОТОЕ ЯБЛОКО")
    logger.info("=" * 60)
    #
    # # Шаг 1: Собираем ссылки на все продукты
    # logger.info("1. Сбор ссылок на продукты...")
    # crawler = Crawler()
    # products = crawler.get_products()
    #
    # # Шаг 2: Сохраняем ссылки в CSV
    # logger.info("2. Сохранение ссылок в CSV...")
    # exporter = CSVExporter(OUTPUT_FILENAME)
    # exporter.export(products)

    # Шаг 3: Парсим детальную информацию о продуктах
    logger.info("3. Парсинг детальной информации о продуктах...")

    # Проверяем, есть ли файл с ссылками
    csv_path = os.path.join("data", OUTPUT_FILENAME)
    if os.path.exists(csv_path):
        parser = Parser()

        if TEST_MODE:
            # В тестовом режиме парсим только первые 1 продуктов
            logger.info("Тестовый режим: парсинг первых 1 продуктов")
            parser.parse_all(limit=1)
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


# def main():
#     """Главный модуль для запуска парсера"""
#     print("\n" + "=" * 60)
#     print("ПАРСИНГ САЙТА ЗОЛОТОЕ ЯБЛОКО")
#     print("=" * 60 + "\n")
#
#     # Шаг 1: Собираем ссылки на все продукты
#     print("1. Сбор ссылок на продукты...")
#
#     attempt = 0
#     products = []
#
#     while attempt < MAX_CRAWLER_ATTEMPTS:
#         attempt += 1
#
#         # НОВОЕ: увеличиваем задержку с каждой новой попыткой
#         # 1-я попытка: 30-60 сек
#         # 2-я попытка: 60-120 сек
#         # 3-я попытка: 120-240 сек и т.д.
#         # вычисляем wait_time
#         wait_time = random.uniform(
#             RETRY_DELAY_MIN * (2 ** (attempt - 1)),  # Увеличиваем в 2 раза с каждой попыткой
#             RETRY_DELAY_MAX * (2 ** (attempt - 1))
#         )
#         # Ограничиваем максимум 5 минутами (300 секунд)
#         # перезаписываем wait_time (более 300 секунд - не будет!)
#         wait_time = min(wait_time, 300)
#
#         print(f"\n🔄 Попытка сбора #{attempt}")
#         if attempt > 1:
#             print(f"⏳ Ждём {wait_time:.0f} секунд перед попыткой (серверу нужно отдохнуть)...")
#             time.sleep(wait_time)
#
#         crawler = Crawler()
#         new_products = crawler.get_products()
#
#         if new_products:
#             products = new_products
#             print(f"✅ Сбор завершён успешно!")
#             break
#         else:
#             print(f"⚠️ Сбор прерван (возможно, сервер временно недоступен)")
#
#     if not products:
#         print(f"❌ Не удалось собрать ссылки после {MAX_CRAWLER_ATTEMPTS} попыток")
#         print(f"💡 Совет: подождите несколько минут и запустите скрипт снова")
#         return
#
#     # Шаг 2: Сохраняем ссылки в CSV
#     print("\n2. Сохранение ссылок в CSV...")
#     exporter = CSVExporter(OUTPUT_FILENAME)
#     exporter.export(products)
#
#     # # Шаг 3: Парсинг (без изменений)
#     # print("\n3. Парсинг детальной информации о продуктах...")
#     # csv_path = os.path.join("data", OUTPUT_FILENAME)
#     # if os.path.exists(csv_path):
#     #     parser = Parser()
#     #     if TEST_MODE:
#     #         print("   Тестовый режим: парсинг первых 1 продуктов")
#     #         parser.parse_all(limit=1)
#     #     else:
#     #         print("   Полный режим: парсинг всех продуктов")
#     #         parser.parse_all()
#     # else:
#     #     print(f"   Файл {csv_path} не найден. Сначала запустите сбор ссылок.")
#
#     print("\n" + "=" * 60)
#     print("ГОТОВО!")
#     print("=" * 60)
#
#
# if __name__ == "__main__":
#     main()






#
#
# # РАБОТАЕТ ДЛЯ crawler.py
# # from src.crawler import Crawler
# # from src.exporter import CSVExporter
# # from src.config import OUTPUT_FILENAME
# #
# #
# # def main():
# #     """Главный модуль для запуска парсера"""
# #     print("\n" + "=" * 60)
# #     print("ПАРСИНГ САЙТА ЗОЛОТОЕ ЯБЛОКО")
# #     print("=" * 60 + "\n")
# #
# #     # Шаг 1: Собираем ссылки на все продукты
# #     print("1. Сбор ссылок на продукты...")
# #     crawler = Crawler()
# #     products = crawler.get_products()
# #
# #     # Шаг 2: Сохраняем в CSV
# #     print("\n2. Сохранение результатов...")
# #     exporter = CSVExporter(OUTPUT_FILENAME)
# #     exporter.export(products)
# #
# #     print("\n" + "=" * 60)
# #     print("ГОТОВО!")
# #     print(f"Собрано ссылок: {len(products)}")
# #     print("=" * 60)
# #
# #
# # if __name__ == "__main__":
# #     main()
# #
# #
# #
# #
# #
# # # from src.crawler import Crawler
# # # from src.exporter import CSVExporter
# # # import logging
# # # import sys
# # # from src.parser import Parser
# # #
# # #
# # # # Настройка логирования
# # # logging.basicConfig(
# # #     level=logging.INFO,
# # #     format='%(asctime)s - %(levelname)s - %(message)s',
# # #     handlers=[
# # #         logging.FileHandler('scraper.log', encoding='utf-8'),
# # #         logging.StreamHandler()
# # #     ]
# # # )
# # # logger = logging.getLogger(__name__)
# # #
# # # # Флаг тестового режима
# # # TEST_MODE = True  # Установите False для полного парсинга
# # #
# # # BASE_URL = "https://goldapple.ru/parfjumerija"
# # # OUTPUT_FILE = "output/goldapple_perfumes.csv"
# # #
# # # # использованы АКУТАЛЬНЫЕ селекторы полей
# # # def main():
# # #     """Запуск тестового режима (3 страницы)"""
# # #     print("\n" + "=" * 60)
# # #     print("🧪 ТЕСТОВЫЙ РЕЖИМ: сбор ссылок с первых 3 страниц")
# # #     print("=" * 60 + "\n")
# # #
# # #     parser = Parser("https://goldapple.ru/parfjumerija", test_mode=True)
# # #     parser.save_to_csv("goldapple_perfumes_test.csv")
# # #
# # #     print("\n" + "=" * 60)
# # #     print("✅ Тестовый режим завершён!")
# # #     print("📁 Результат сохранён в файл: goldapple_perfumes_test.csv")
# # #     print("=" * 60)
# # #
# # #     # # Базовый сборщик — только ссылки
# # #     # parser = Parser("https://goldapple.ru/parfjumerija")
# # #     # parser.save_to_csv("goldapple_perfumes.csv")
# # #
# # #     # # Использование
# # #     # parser = Parser("https://goldapple.ru/parfjumerija")
# # #     # product_url = parser.find_product_url()
# # #     # print(product_url)
# # #
# # #     # # Инициализация парсера
# # #     # parser = Parser(url=BASE_URL)
# # #     # parser.fetch_page()
# # #
# # #
# # # #     logger.info("Запуск скрапинга Gold Apple Парфюмерия")
# # # #
# # # #     # Инициализация краулера (задержка 2 секунды между запросами)
# # # #     crawler = Crawler(
# # # #         base_url=BASE_URL,
# # # #         delay=2,
# # # #         test_mode=TEST_MODE  # Передаём значение глобальной переменной
# # # #     )
# # # #
# # # #     # products = crawler.crawl(max_pages=3)  # Сканирование 3 страниц для теста
# # # #     try:
# # # #         products = crawler.crawl(max_pages=None)  # Запускаем автоопределение
# # # #         logger.info(f"Собрано товаров: {len(products)}")
# # # #
# # # #         # Экспорт в CSV
# # # #         exporter = CSVExporter(OUTPUT_FILE)
# # # #         exporter.export(products)
# # # #
# # # #         logger.info(f"Данные успешно сохранены в {OUTPUT_FILE}")
# # # #
# # # #     except Exception as e:
# # # #         logger.critical(f"Критическая ошибка при выполнении скрапинга: {e}")
# # #
# # # if __name__ == "__main__":
# # #     main()
