"""Конфигурация парсера - селекторы и настройки"""

# Базовые URL
BASE_URL = "https://goldapple.ru/parfjumerija"  # РАЗДЕЛ САЙТА ДЛЯ ПАРСИНГА
OUTPUT_FILENAME = "goldapple_perfumes.csv"  # Имя выходного CSV-файла

# Настройки парсинга
TEST_MODE = True  # Установить False для полной пагинации
TEST_MODE_PAGES = 2  # Установить количество страниц для тестовой пагинации (увеличьте для отладки отбоя сервером)
DEFAULT_MAX_PAGES = 500  # Количество страниц принудительного прерывания пагинации

# Настройки задержек (в секундах)
REQUEST_DELAY_MIN = 2.0      # 2 секунды между запросами на странице
REQUEST_DELAY_MAX = 4.0      # до 4 секунд
PAGE_DELAY_MIN = 3.0         # 3 секунды между страницами
PAGE_DELAY_MAX = 6.0         # до 6 секунд
RETRY_DELAY_MIN = 10.0       # 10 секунд перед повторной попыткой
RETRY_DELAY_MAX = 20.0       # до 20 секунд
# REQUEST_DELAY_MIN = 0.3  # Нижняя граница случайного диапазона запросов к серверу
# REQUEST_DELAY_MAX = 3.0  # Верхняя граница случайного диапазона запросов к серверу
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
    # Цена
    "product_price": [
        "._ga-price_1dj1y_114",
        "[itemprop='price']",
        "._ga-pdp-price-guest__price_1mmpu_157 ._ga-price_1dj1y_114",
        "[class*='_ga-price']",
    ],

    # Описание продукта (из блока wysiwyg)
    "product_description": [
        "._ga-pdp-wysiwyg_rmnt6_55",
        "[itemprop='description']",
    ],
}

# СЕЛЕКТОРЫ ДЛЯ СТРАНИЦЫ ОТЗЫВОВ (REVIEW)
SELECTORS_REVIEW = {
    # Рейтинг товара (из вашего HTML)
    "product_rating": [
        "._ga-review-score-point__numeral",
        "[itemprop='ratingValue']",
    ],
}
