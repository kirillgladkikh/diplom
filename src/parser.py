import requests
from src.product import Product
from bs4 import BeautifulSoup
import re
# import time


# использованы АКУТАЛЬНЫЕ селекторы полей
class Parser:
    def __init__(self, url):
        self.url = url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_page(self):
        response = self.session.get(self.url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')

    @staticmethod
    def parse_product_list(soup):
        """Парсинг списка товаров на странице каталога — извлекаем URL товаров"""
        products = []  # Инициализируем пустой список для хранения данных о товарах
        cards = soup.select('a.product-card__link')  # Находим все ссылки с карточками товаров по CSS‑селектору

        for card in cards:  # Перебираем каждую карточку товара в найденном списке
            # Извлекаем URL товара
            href = card.get('href')  # Получаем значение атрибута 'href' из тега <a>
            if not href:  # Проверяем, существует ли атрибут href
                continue  # Если href отсутствует, пропускаем текущую итерацию цикла — переходим к следующей карточке

            # Формируем полный URL товара:
            # Если ссылка относительная (начинается с '/'), добавляем базовый домен
            # В противном случае используем ссылку как есть
            product_url = 'https://goldapple.ru' + href if href.startswith('/') else href
            # product_url = 'https://goldapple.ru' + card['href']

            # Извлекаем название товара (если доступно)
            name_elem = card.select_one('span.product-card__name')  # Ищем элемент с названием товара внутри карточки
            # Если элемент найден, берём его текст и убираем лишние пробелы; иначе — ставим заглушку
            name = name_elem.text.strip() if name_elem else 'Не указано'

            # Извлекаем цену товара (если доступна)
            price_elem = card.select_one('span.current-price')  # Ищем элемент с текущей ценой
            # Если элемент найден, удаляем все нецифровые символы из текста (оставляем только цифры цены);
            # иначе устанавливаем цену '0'
            price = re.sub(r'\D', '', price_elem.text) if price_elem else '0'

            # Извлекаем рейтинг товара (если доступен)
            rating_elem = card.select_one('div.rating__stars')  # Ищем элемент со звездой рейтинга
            # Если элемент найден, получаем значение атрибута 'data-rating'; иначе — ставим '0'
            rating = rating_elem.get('data-rating', '0') if rating_elem else '0'

            # name = name_elem.text.strip() if name_elem else 'Не указано'
            # price = re.sub(r'\D', '', price_elem.text) if price_elem else '0'
            # rating = rating_elem['data-rating'] if rating_elem and rating_elem.get('data-rating') else '0'

            # Добавляем словарь с данными о текущем товаре в общий список
            products.append({
                'url': product_url,  # URL страницы товара
                'name': name,  # Название товара
                'price': price,  # Цена (только цифры)
                'rating': rating  # Рейтинг (значение из data-rating)
            })
        return products  # Возвращаем список словарей с информацией о всех найденных товарах

    def parse_product_detail(self, soup, product_url):
        """Парсинг детальной информации о товаре"""
        # Наименование (полное)
        name_elem = soup.select_one('h1.product-main__title')
        name = name_elem.text.strip() if name_elem else 'Не указано'

        # Цена
        price_elem = soup.select_one('span.current-price, div.price__current')
        price = re.sub(r'\D', '', price_elem.text) if price_elem else '0'

        # Описание
        desc_elem = soup.select_one('div.product-description__content')
        description = desc_elem.get_text(strip=True) if desc_elem else 'Нет описания'

        # Инструкция по применению
        instruction_header = soup.find('h3', string=re.compile(r'Способ применения', re.IGNORECASE))
        instructions = 'Нет инструкции'
        if instruction_header:
            next_elem = instruction_header.find_next('div')
            if next_elem:
                instructions = next_elem.get_text(strip=True)

        # Страна-производитель
        country_elem = soup.find('span', string=re.compile(r'Страна производства', re.IGNORECASE))
        country = 'Не указано'
        if country_elem:
            # Ищем следующий элемент с информацией
            country_value = country_elem.find_next('span')
            if country_value:
                country = country_value.get_text(strip=True)

        return Product(
            url=product_url,
            name=name,
            price=price,
            rating=self._get_rating_from_detail(soup),
            description=description,
            instructions=instructions,
            country=country
        )

    @staticmethod
    def _get_rating_from_detail(soup):
        """Извлечение рейтинга со страницы товара"""
        rating_elem = soup.select_one('div.rating__value')
        if rating_elem:
            rating_text = rating_elem.get_text()
            match = re.search(r'\d+\.?\d*', rating_text)
            return match.group() if match else '0'
        return '0'
