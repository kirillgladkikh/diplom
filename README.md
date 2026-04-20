# ДИПЛОМНЫЙ ПРОЕКТ
# Кирилл Гладких
# Веб-скрапинг информации о товарах (BB1)

## Описание проекта
- Проект реализует автоматизированный сбор данных о парфюмерии с сайта Gold Apple (https://goldapple.ru/parfjumerija). 
- Собираются следующие данные: ссылка на продукт, наименование, цена, рейтинг, описание, инструкция по применению и страна-производитель.

### Описание задачи:
- Есть сайт со списком товаров, рейтингом, условиями его применения и прочей информацией, которая помогает пользователю сделать выбор при покупке. 
- Вы разрабатываете новый онлайн-магазин и вам необходимо определить, какие товары имеют наибольшую ценность для пользователя по совокупности параметров. 
- Это поможет:
- Закупить эти товары для продажи.
- Активно продвигать их в рекламе и получать прибыль.

### Задача
- Создать CSV файл со всеми товарами из раздела "Парфюмерия" магазина: [Gold Apple - Парфюмерия](https://goldapple.ru/parfjumerija).
- В этом файле должна быть следующая информация в текстовом формате:

1. Ссылка на продукт
2. Наименование
3. Цена
4. Рейтинг пользователей
5. Описание продукта
6. Инструкция по применению
7. Страна-производитель

### Технические требования:

1. **Язык программирования**: 
   - Использовать Python 3.11 и выше для реализации проекта.
2. **Сбор данных**: 
   - Реализовать веб-скрапинг для сбора информации о товарах.
3. **Формат данных**: 
   - Сохранить данные в CSV формате.
4. **Обработка данных**: 
   - Использовать регулярные выражения для парсинга данных.
5. **Архитектура**: 
   - Реализовать проект с использованием объектно-ориентированного подхода.
6. **Документация**: 
   - В корне проекта должен быть файл README.md с описанием структуры проекта и инструкциями по установке и запуску.
7. **Качество кода**: 
   - Соблюдать стандарты PEP8.
   - Весь код должен храниться в удаленном Git репозитории.
8. **Тестирование**: 
   - Код должен быть покрыт тестами с покрытием не менее 75%.
9. **Итоговая выгрузка**: 
   - Итоговый CSV файл должен быть приложен к README.md.

## Структура проекта
- `main.py` — точка входа;
- `src/` — исходный код (модели, парсер, краулер, экспортер);
- `src/config.py` - глобальные переменные и селекторы
- `src/product.py` - модель товара
- `src/crawler.py` - клаулер ссылок на товары
- `src/parser.py` - парсер данных о товаре
- `src/exporter.py` - сохраняет данные о товарах в итоговый CSV файл
- `tests/` — модульные тесты;
- `tests/test_product.py`
- `tests/test_crawler.py`
- `tests/test_parser.py`
- `tests/test_exporter.py`
- `data/` — директория для выходного файла CSV [goldapple_perfumes.csv](data%2Fgoldapple_perfumes.csv);
- `requirements.txt` — зависимости проекта;
- `README.md` — документация.

## Иерархия методов классов
### Product
```
Product
│
├── __init__(url, name, price, rating, description, instructions, country)
│
└── to_dict()                         # преобразование в словарь
    └── (использует атрибуты экземпляра)
```
### Crawler
```
Crawler
│
├── __init__()
│
├── get_products()                    # публичный метод
│   └── collect_all_links()           # вызывается внутри
│
├── collect_all_links(resume)         # основной метод краулинга
│   ├── _init_driver()                # ←
│   ├── _load_checkpoint()            # ← если resume=True
│   ├── _extract_links_from_page()    # ← в цикле для каждой страницы
│   │   └── _random_delay()           # ← внутри _extract_links_from_page
│   ├── _check_empty_page()           # ← проверка пустых страниц
│   ├── _save_checkpoint()            # ← после каждой страницы
│   ├── _random_delay()               # ← между страницами
│   └── _clear_checkpoint()           # ← после успешного завершения
│
├── _init_driver()                    # вызывается из collect_all_links
│
├── _save_checkpoint()                # вызывается из collect_all_links
│
├── _load_checkpoint()                # вызывается из collect_all_links
│
├── _clear_checkpoint()               # вызывается из collect_all_links
│
├── _random_delay()                   # вызывается из _extract_links_from_page и collect_all_links
│
├── _extract_links_from_page()        # вызывается из collect_all_links
│   └── _random_delay()               # ←
│
└── _check_empty_page()               # вызывается из collect_all_links
```
### Parser
```
Parser
│
├── __init__(input_filename, data_dir)
│
├── parse_all(start_from, limit)      # основной публичный метод
│   ├── load_products_from_csv()      # ←
│   ├── _init_driver()                # ←
│   ├── parse_product()               # ← в цикле
│   │   ├── _safe_get()               # ←
│   │   │   ├── _random_delay()       # ←
│   │   │   ├── restart_driver()      # ← при ошибке
│   │   │   │   └── _init_driver()    # ←
│   │   │   └── debug_save_page_source() # ← опционально
│   │   ├── _get_product_name()       # ←
│   │   ├── _get_price()              # ←
│   │   │   └── _get_text()           # ←
│   │   ├── _get_description()        # ←
│   │   │   └── _get_text()           # ←
│   │   ├── _get_instructions()       # ←
│   │   ├── _get_country()            # ←
│   │   └── _get_rating_from_review_page() # ←
│   └── save_products_to_csv()        # ← после каждого продукта
│
├── parse_missing_only()              # альтернативный метод
│   ├── load_products_from_csv()      # ←
│   ├── _init_driver()                # ←
│   ├── parse_product()               # ← для пропущенных
│   └── save_products_to_csv()        # ←
│
├── load_products_from_csv()          # вызывается из parse_all/parse_missing_only
│
├── save_products_to_csv()            # вызывается из parse_all/parse_missing_only
│
├── parse_product(product)            # вызывается из parse_all/parse_missing_only
│   ├── _safe_get()                   # ←
│   ├── _get_product_name()           # ←
│   ├── _get_price()                  # ←
│   ├── _get_description()            # ←
│   ├── _get_instructions()           # ←
│   ├── _get_country()                # ←
│   └── _get_rating_from_review_page() # ←
│
├── _safe_get(url)                    # вызывается из parse_product
│   ├── _init_driver()                # ← если driver None
│   ├── _random_delay()               # ←
│   └── restart_driver()              # ← при ошибке
│
├── restart_driver()                  # вызывается из _safe_get
│   └── _init_driver()                # ←
│
├── _init_driver()                    # вызывается из restart_driver и _safe_get
│
├── _random_delay()                   # вызывается из _safe_get
│
├── _get_text(selectors)              # вызывается из _get_price, _get_description
│
├── _get_product_name()               # вызывается из parse_product
│
├── _get_price()                      # вызывается из parse_product
│   └── _get_text()                   # ←
│
├── _get_description()                # вызывается из parse_product
│   └── _get_text()                   # ←
│
├── _get_rating_from_review_page()    # вызывается из parse_product
│   └── _random_delay()               # ← (через time.sleep)
│
├── _get_instructions()               # вызывается из parse_product
│   └── (работа с driver и regex)
│
├── _get_country()                    # вызывается из parse_product
│   └── (работа с driver и regex)
│
└── debug_save_page_source()          # вызывается из _safe_get
```
### Exporter
```
CSVExporter
│
├── __init__(filename, data_dir)
│
├── get_full_path()                   # вспомогательный метод
│
└── export(products)                  # публичный метод
    ├── get_full_path()               # ← получает путь к файлу
    └── (работа с CSV через to_dict() продуктов)
```

## Установка
1. Клонируйте репозиторий: `git clone https://github.com/kirillgladkikh/diplom.git`
2. Установите зависимости: `pip install -r requirements.txt`
3. Создайте виртуальное окружение (рекомендуется): `python -m venv venv`
4. Активируйте окружение: `source venv/bin/activate` (Linux/Mac) или `venv\Scripts\

Проект можно запускать на любом компьютере через:
```
powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```
## Документация:
Настоящий файл [README.md](README.md).

## Лицензия:
Проект распространяется под [лицензией MIT](LICENSE). 
