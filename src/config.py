"""Конфигурация парсера - селекторы и настройки"""

# Базовые настройки
BASE_URL = "https://goldapple.ru/parfjumerija"  # РАЗДЕЛ САЙТА ДЛЯ ПАРСИНГА
OUTPUT_FILENAME = "goldapple_perfumes.csv"  # Имя выходного CSV-файла
CRAWLER_CHECKPOINT_FILE = "crawler_checkpoint.json"  # Файл для сохранения прогресса
CRAWLER_SAVE_EVERY_PAGES = 10  # Сохранять после каждых N страниц
MAX_EMPTY_PAGES = 3  # Сколько пустых страниц подряд считать концом каталога

# Настройки парсинга
TEST_MODE = False  # Установить False для полной пагинации
TEST_MODE_PAGES = 5  # Установить количество страниц для тестовой пагинации (увеличьте для отладки отбоя сервером)
DEFAULT_MAX_PAGES = 3000  # Количество страниц принудительного прерывания пагинации
MAX_CRAWLER_ATTEMPTS = 10  # Максимум попыток собрать ссылки


# Настройки задержек (в секундах)
REQUEST_DELAY_MIN = 2.0  # 2 секунды между запросами на странице
REQUEST_DELAY_MAX = 4.0  # до 4 секунд
PAGE_DELAY_MIN = 5.0  # 5 секунды между страницами
PAGE_DELAY_MAX = 10.0  # до 10 секунд
RETRY_DELAY_MIN = 30.0  # 30 секунд перед повторной попыткой
RETRY_DELAY_MAX = 60.0  # до 60 секунд
RETRY_COUNT = 3  # Задержка при сбое доступа к серверу при пагинации

# СЕЛЕКТОРЫ ДЛЯ СТРАНИЦЫ КАТАЛОГА (PLP)
SELECTORS_PLP = {
    # Паттерн для определения ссылки на продукт по структуре URL
    "product_link_pattern": r"/\d+-[a-z0-9-]+$",
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
