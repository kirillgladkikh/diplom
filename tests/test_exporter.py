import os
import tempfile

from src.exporter import CSVExporter
from src.product import Product


class TestCSVExporter:
    """Тесты для CSVExporter"""

    def setup_method(self):
        """Создаем временную директорию для тестов"""
        self.temp_dir = tempfile.mkdtemp()

    def test_init_creates_directory(self):
        """Тест: инициализация создает директорию"""
        exporter = CSVExporter("test.csv", self.temp_dir)
        assert os.path.exists(self.temp_dir)

    def test_get_full_path(self):
        """Тест: получение полного пути к файлу"""
        exporter = CSVExporter("test.csv", self.temp_dir)
        expected = os.path.join(self.temp_dir, "test.csv")
        assert exporter.get_full_path() == expected

    def test_export_empty_products(self):
        """Тест: экспорт пустого списка продуктов"""
        exporter = CSVExporter("empty.csv", self.temp_dir)
        result = exporter.export([])
        assert result is False

    def test_export_single_product(self):
        """Тест: экспорт одного продукта"""
        exporter = CSVExporter("single.csv", self.temp_dir)

        products = [
            Product(
                url="https://test.ru/1",
                name="Product 1",
                price="100",
                rating="4.5",
                description="Desc 1",
                instructions="Instr 1",
                country="Russia",
            )
        ]

        result = exporter.export(products)
        assert result is True

        # Проверяем, что файл создан
        full_path = exporter.get_full_path()
        assert os.path.exists(full_path)

        # Проверяем содержимое
        with open(full_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
            assert "Ссылка на продукт" in content
            assert "https://test.ru/1" in content
            assert "Product 1" in content

    def test_export_multiple_products(self):
        """Тест: экспорт нескольких продуктов"""
        exporter = CSVExporter("multiple.csv", self.temp_dir)

        products = [
            Product(url="https://test.ru/1", name="Product 1"),
            Product(url="https://test.ru/2", name="Product 2"),
            Product(url="https://test.ru/3", name="Product 3"),
        ]

        result = exporter.export(products)
        assert result is True

        full_path = exporter.get_full_path()
        assert os.path.exists(full_path)

        # Считаем строки (минус заголовок)
        with open(full_path, "r", encoding="utf-8-sig") as f:
            lines = f.readlines()
            # Заголовок + 3 продукта
            assert len(lines) == 4

    def test_export_with_existing_directory(self):
        """Тест: экспорт когда директория уже существует"""
        # Создаем директорию заранее
        os.makedirs(self.temp_dir, exist_ok=True)

        exporter = CSVExporter("existing.csv", self.temp_dir)
        products = [Product(url="https://test.ru/1")]

        result = exporter.export(products)
        assert result is True
        assert os.path.exists(exporter.get_full_path())
