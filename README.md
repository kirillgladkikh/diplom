# ДИПЛОМНЫЙ ПРОЕКТ
# Кирилл Гладких
# Веб-скрапинг информации о товарах (BB1)

## Описание проекта
Проект реализует автоматизированный сбор данных о парфюмерии с сайта Gold Apple (https://goldapple.ru/parfjumerija). Собираются следующие данные: ссылка на продукт, наименование, цена, рейтинг, описание, инструкция по применению и страна-производитель.

## Структура проекта
- `src/` — исходный код (модели, парсер, краулер, экспортер);
- `tests/` — модульные тесты;
- `output/` — директория для выходных файлов;
- `main.py` — точка входа;
- `requirements.txt` — зависимости проекта;
- `README.md` — документация.

## Установка
1. Клонируйте репозиторий: `git clone https://github.com/kirillgladkikh/diplom.git`
2. Установите зависимости: `pip install -r requirements.txt`
3. Создайте виртуальное окружение (рекомендуется): `python -m venv venv`
4. Активируйте окружение: `source venv/bin/activate` (Linux/Mac) или `venv\Scripts\

Теперь проект можно запускать на любом компьютере через:
```
powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```