import pytest

from src.product import Product


class TestProduct:
    """Тесты для класса Product"""

    def test_product_creation_with_all_fields(self):
        """Тест создания продукта со всеми полями"""
        product = Product(
            url="https://goldapple.ru/123-product",
            name="Test Perfume",
            price="999",
            rating="4.5",
            description="Test description",
            instructions="Test instructions",
            country="France",
        )

        assert product.url == "https://goldapple.ru/123-product"
        assert product.name == "Test Perfume"
        assert product.price == "999"
        assert product.rating == "4.5"
        assert product.description == "Test description"
        assert product.instructions == "Test instructions"
        assert product.country == "France"

    def test_product_creation_with_minimal_fields(self):
        """Тест создания продукта только с URL"""
        product = Product(url="https://goldapple.ru/123-product")

        assert product.url == "https://goldapple.ru/123-product"
        assert product.name is None
        assert product.price is None
        assert product.rating is None
        assert product.description is None
        assert product.instructions is None
        assert product.country is None

    def test_product_creation_empty(self):
        """Тест создания пустого продукта"""
        product = Product()

        assert product.url is None
        assert product.name is None
        assert product.price is None

    def test_to_dict_with_all_fields(self):
        """Тест конвертации в словарь со всеми полями"""
        product = Product(
            url="https://goldapple.ru/123",
            name="Test",
            price="1000",
            rating="5",
            description="Desc",
            instructions="Instr",
            country="Russia",
        )

        result = product.to_dict()

        assert result["Ссылка на продукт"] == "https://goldapple.ru/123"
        assert result["Наименование"] == "Test"
        assert result["Цена"] == "1000"
        assert result["Рейтинг пользователей"] == "5"
        assert result["Описание продукта"] == "Desc"
        assert result["Инструкция по применению"] == "Instr"
        assert result["Страна-производитель"] == "Russia"

    def test_to_dict_with_missing_fields(self):
        """Тест конвертации в словарь с отсутствующими полями"""
        product = Product(url="https://goldapple.ru/123")

        result = product.to_dict()

        assert result["Ссылка на продукт"] == "https://goldapple.ru/123"
        assert result["Наименование"] == "нет"
        assert result["Цена"] == "нет"
        assert result["Рейтинг пользователей"] == "нет"
        assert result["Описание продукта"] == "нет"
        assert result["Инструкция по применению"] == "нет"
        assert result["Страна-производитель"] == "нет"

    def test_csv_headers_constant(self):
        """Тест наличия заголовков CSV"""
        assert Product.CSV_HEADERS == [
            "Ссылка на продукт",
            "Наименование",
            "Цена",
            "Рейтинг пользователей",
            "Описание продукта",
            "Инструкция по применению",
            "Страна-производитель",
        ]
        assert len(Product.CSV_HEADERS) == 7
