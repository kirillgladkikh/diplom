from .parser import Parser
from urllib.parse import urljoin
import time
import logging


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Crawler:
    def __init__(self, base_url, delay=2):
        self.base_url = base_url
        self.delay = delay
        self.parser = Parser(base_url)

    def get_product_urls(self, page_url):
        soup = self.parser.fetch_page()
        product_links = []
        for link in soup.select('a.product-card__link'):
            href = link['href']
            full_url = urljoin(self.base_url, href)
            product_links.append(full_url)
        return product_links

    def crawl(self, max_pages=5):
        all_products = []

        for page_num in range(1, max_pages + 1):
            page_url = f"{self.base_url}?page={page_num}"
            print(f"Парсинг страницы {page_num}: {page_url}")

            # Парсим список товаров на странице
            soup = self.parser.fetch_page()
            product_list = self.parser.parse_product_list(soup)

            for product_info in product_list:
                # Парсим детальную информацию о товаре
                detail_parser = Parser(product_info['url'])
                detail_soup = detail_parser.fetch_page()
                product = detail_parser.parse_product_detail(detail_soup, product_info['url'])

                # Обновляем данные из каталога, если нужно
                if product.price == '0':
                    product.price = product_info['price']
                if product.rating == '0':
                    product.rating = product_info['rating']

                all_products.append(product)
                time.sleep(self.delay)  # Задержка для избежания блокировки

        return all_products
