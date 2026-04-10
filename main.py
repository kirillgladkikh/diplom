def main():
    BASE_URL = "https://goldapple.ru/parfjumerija"
    logger.info(f"Проверяем формат URL товаров на {BASE_URL}")

    # Быстрая проверка: берём первую страницу, парсим 1–2 товара
    test_crawler = Crawler(BASE_URL, delay=2, test_mode=True)
    test_products = test_crawler.crawl(max_pages=1)  # Только 1 страница

    if test_products:
        sample_url = test_products[0].url
        logger.info(f"Образец URL товара: {sample_url}")
        if '/catalog/product/view/' in sample_url:
            logger.critical("Формат URL запрещён robots.txt. Прекращаем парсинг.")
            return
        else:
            logger.info("Формат URL безопасен. Запускаем полный парсинг...")
            # Запускаем основной парсинг
            full_crawler = Crawler(BASE_URL, delay=2, test_mode=False)
            products = full_crawler.crawl()
            # Экспорт и т. д.
    else:
        logger.error("Не удалось получить тестовые данные. Проверьте подключение.")
