"""Конфигурация парсера - селекторы и настройки"""

# Базовые URL
BASE_URL = "https://goldapple.ru/parfjumerija"  # РАЗДЕЛ САЙТА ДЛЯ ПАРСИНГА
OUTPUT_FILENAME = "goldapple_perfumes.csv"  # Имя выходного CSV-файла

# Настройки парсинга
TEST_MODE = True  # Установить False для полной пагинации
TEST_MODE_PAGES = 3  # Установить количество страниц для тестовой пагинации (увеличьте для отладки отбоя сервером)
DEFAULT_MAX_PAGES = 500  # Количество страниц принудительного прерывания пагинации
REQUEST_DELAY_MIN = 0.3  # Нижняя граница случайного диапазона запросов к серверу
REQUEST_DELAY_MAX = 1.5  # Верхняя граница случайного диапазона запросов к серверу
RETRY_COUNT = 3  # Задержка при сбое доступа к серверу при пагинации

# СЕЛЕКТОРЫ ДЛЯ СТРАНИЦЫ КАТАЛОГА (PLP)
SELECTORS_PLP = {
    # Паттерн для определения ссылки на продукт по структуре URL
    "product_link_pattern": r'/\d+-[a-z0-9-]+$',

    # Контейнер пагинации
    "pagination_container": "ul._ga-plp-pagination_1ert2_1",
}

# СЕЛЕКТОРЫ ДЛЯ СТРАНИЦЫ ТОВАРА (PDP)
SELECTORS_PDP = {
    # Наименование продукта
    "product_name": ["h1"],

    # Цена
    "product_price": [
        "[itemprop='price']",
        "._ga-price_1dj1y_114",
    ],

    # Рейтинг
    "product_rating": ["[class*='rating-value']"],

    # Описание
    "product_description": ["[itemprop='description']"],

    # Инструкция по применению
    "product_instructions": [
        "//h2[contains(text(), 'Применение')]/ancestor::section//div[contains(@class, 'wysiwyg')]"
    ],

    # Страна-производитель
    "product_country": [
        "//div[contains(@class, 'wysiwyg')]//text()[contains(., 'страна')]"
    ],
}
