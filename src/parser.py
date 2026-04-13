import requests
from src.product import Product
from bs4 import BeautifulSoup
import re
import time

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

    def parse_product_list(self, soup):
        """Парсинг списка товаров на странице каталога"""
        products = []
        cards = soup.select('a.product-card__link')
        for card in cards:
            product_url = 'https://goldapple.ru' + card['href']
            name_elem = card.select_one('span.product-card__name')
            price_elem = card.select_one('span.current-price')
            rating_elem = card.select_one('div.rating__stars')

            name = name_elem.text.strip() if name_elem else 'Не указано'
            price = re.sub(r'[^\d]', '', price_elem.text) if price_elem else '0'
            rating = rating_elem['data-rating'] if rating_elem and rating_elem.get('data-rating') else '0'

            products.append({
                'url': product_url,
                'name': name,
                'price': price,
                'rating': rating
            })
        return products

    def parse_product_detail(self, soup, product_url):
        """Парсинг детальной информации о товаре"""
        # Наименование (полное)
        name_elem = soup.select_one('h1.product-main__title')
        name = name_elem.text.strip() if name_elem else 'Не указано'

        # Цена
        price_elem = soup.select_one('span.current-price, div.price__current')
        price = re.sub(r'[^\d]', '', price_elem.text) if price_elem else '0'

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

    def _get_rating_from_detail(self, soup):
        """Извлечение рейтинга со страницы товара"""
        rating_elem = soup.select_one('div.rating__value')
        if rating_elem:
            rating_text = rating_elem.get_text()
            match = re.search(r'\d+\.?\d*', rating_text)
            return match.group() if match else '0'
        return '0'
