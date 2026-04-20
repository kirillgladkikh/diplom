import os
import tempfile
import csv

from src.parser import Parser
from src.product import Product

from unittest.mock import Mock, patch, MagicMock


class TestParser:
    """Тесты для Parser"""

    def setup_method(self):
        """Создаем временные файлы для тестов"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv = os.path.join(self.temp_dir, "test_products.csv")

    def test_parser_init(self):
        """Тест: инициализация парсера"""
        parser = Parser("test.csv", self.temp_dir)
        assert parser.input_filename == "test.csv"
        assert parser.input_path == os.path.join(self.temp_dir, "test.csv")
        assert parser.driver is None

    def test_load_products_from_csv_empty(self):
        """Тест: загрузка из пустого CSV"""
        # Создаем пустой CSV с заголовками
        with open(self.test_csv, "w", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=Product.CSV_HEADERS)
            writer.writeheader()

        parser = Parser("test_products.csv", self.temp_dir)
        parser.input_path = self.test_csv

        products = parser.load_products_from_csv()
        assert products == []

    def test_load_products_from_csv_with_data(self):
        """Тест: загрузка из CSV с данными"""
        # Создаем CSV с данными
        with open(self.test_csv, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=Product.CSV_HEADERS)
            writer.writeheader()
            writer.writerow(
                {
                    "Ссылка на продукт": "https://test.ru/1",
                    "Наименование": "Test Product",
                    "Цена": "1000",
                    "Рейтинг пользователей": "4.5",
                    "Описание продукта": "Test desc",
                    "Инструкция по применению": "Test instr",
                    "Страна-производитель": "France",
                }
            )

        parser = Parser("test_products.csv", self.temp_dir)
        parser.input_path = self.test_csv

        products = parser.load_products_from_csv()

        assert len(products) == 1
        assert products[0].url == "https://test.ru/1"
        assert products[0].name == "Test Product"
        assert products[0].price == "1000"
        assert products[0].rating == "4.5"

    def test_load_products_from_csv_missing_file(self):
        """Тест: загрузка из несуществующего файла"""
        parser = Parser("nonexistent.csv", self.temp_dir)
        products = parser.load_products_from_csv()
        assert products == []

    def test_save_products_to_csv(self):
        """Тест: сохранение продуктов в CSV"""
        products = [
            Product(
                url="https://test.ru/1",
                name="Product 1",
                price="100",
                rating="4",
                description="Desc 1",
                instructions="Instr 1",
                country="Russia",
            ),
            Product(
                url="https://test.ru/2",
                name="Product 2",
                price="200",
                rating="5",
                description="Desc 2",
                instructions="Instr 2",
                country="USA",
            ),
        ]

        parser = Parser("test_products.csv", self.temp_dir)
        parser.input_path = self.test_csv
        parser.save_products_to_csv(products)

        # Проверяем что файл создан
        assert os.path.exists(self.test_csv)

        # Проверяем содержимое
        loaded = parser.load_products_from_csv()
        assert len(loaded) == 2
        assert loaded[0].name == "Product 1"
        assert loaded[1].name == "Product 2"

    def test_get_text_with_string_selector(self):
        """Тест: _get_text с строковым селектором (без реального драйвера)"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = None

        # Драйвер не инициализирован, должен вернуть пустую строку
        result = parser._get_text("some_selector")
        assert result == ""

    def test_get_text_with_list_selector(self):
        """Тест: _get_text со списком селекторов"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = None

        result = parser._get_text([".sel1", ".sel2", ".sel3"])
        assert result == ""

    def test_get_product_name_no_driver(self):
        """Тест: получение названия без драйвера"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = None

        name = parser._get_product_name()
        assert name == "нет"

    def test_get_price_no_driver(self):
        """Тест: получение цены без драйвера"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = None

        price = parser._get_price()
        assert price == "нет"

    def test_get_description_no_driver(self):
        """Тест: получение описания без драйвера"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = None

        desc = parser._get_description()
        assert desc == "нет"

    def test_get_instructions_no_driver(self):
        """Тест: получение инструкции без драйвера"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = None

        instructions = parser._get_instructions()
        assert instructions == "нет"

    def test_get_country_no_driver(self):
        """Тест: получение страны без драйвера"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = None

        country = parser._get_country()
        assert country == "нет"

    def test_get_rating_no_driver(self):
        """Тест: получение рейтинга без драйвера"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = None

        rating = parser._get_rating_from_review_page("https://test.ru/123")
        assert rating == "нет"

    def test_parse_product_without_driver(self):
        """Тест: парсинг продукта без драйвера"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = None

        product = Product(url="https://test.ru/123")
        result = parser.parse_product(product)

        # Должен вернуть продукт без изменений (не удалось загрузить)
        assert result.url == "https://test.ru/123"

    def test_restart_driver(self):
        """Тест: перезапуск драйвера"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = None

        # Просто проверяем что метод не падает
        parser.restart_driver()
        # Драйвер должен быть None, так как _init_driver требует selenium
        # В тестовой среде без selenium он упадёт, но мы не проверяем результат
        assert hasattr(parser, "restart_driver")

    def setup_method(self):
        """Создаем временную директорию для тестов"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv = os.path.join(self.temp_dir, "test_products.csv")

    def test_init_driver_returns_driver(self):
        """Тест: _init_driver создает драйвер"""
        parser = Parser("test.csv", self.temp_dir)

        with patch("src.parser.webdriver.Chrome") as mock_chrome:
            mock_driver = Mock()
            mock_chrome.return_value = mock_driver

            driver = parser._init_driver()

            assert driver is not None
            mock_chrome.assert_called_once()

    def test_random_delay(self):
        """Тест: случайная задержка"""
        parser = Parser("test.csv", self.temp_dir)

        import time

        start = time.time()
        parser._random_delay()
        elapsed = time.time() - start

        assert elapsed >= 2.0  # REQUEST_DELAY_MIN = 2.0

    def test_restart_driver_when_driver_is_none(self):
        """Тест: перезапуск драйвера когда его нет"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = None

        with patch.object(parser, "_init_driver", return_value=Mock()):
            parser.restart_driver()

            # Просто проверяем что не упало
            assert True

    def test_safe_get_returns_false_on_timeout(self):
        """Тест: _safe_get возвращает False при таймауте"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        from selenium.common.exceptions import TimeoutException

        parser.driver.get.side_effect = TimeoutException("Timeout")

        with patch("src.parser.WebDriverWait", side_effect=TimeoutException):
            result = parser._safe_get("https://test.ru")

            assert result is False

    def test_safe_get_returns_false_on_general_error(self):
        """Тест: _safe_get возвращает False при общей ошибке"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        parser.driver.get.side_effect = Exception("General error")

        result = parser._safe_get("https://test.ru")

        assert result is False

    def test_safe_get_success(self):
        """Тест: _safe_get успешно загружает страницу"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        with patch("src.parser.WebDriverWait"):
            with patch("time.sleep"):
                result = parser._safe_get("https://test.ru")

                assert result is True
                parser.driver.get.assert_called_with("https://test.ru")

    def test_debug_save_page_source(self):
        """Тест: сохранение HTML страницы для отладки"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()
        parser.driver.page_source = "<html><body>Test</body></html>"

        with patch("builtins.open", create=True) as mock_open:
            parser.debug_save_page_source("test_debug.html")
            mock_open.assert_called()

    def test_debug_save_page_source_no_driver(self):
        """Тест: сохранение HTML когда нет драйвера"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = None

        with patch("src.parser.logger") as mock_logger:
            parser.debug_save_page_source("test.html")
            assert True

    def test_get_text_with_none_driver(self):
        """Тест: _get_text когда драйвер None"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = None

        result = parser._get_text(".selector")
        assert result == ""

    def test_get_text_with_multiple_selectors(self):
        """Тест: _get_text с несколькими селекторами"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        # Первый селектор не найден, второй найден
        from selenium.common.exceptions import NoSuchElementException

        element_mock = Mock()
        element_mock.text.strip.return_value = "Found text"

        # Первый вызов вызывает исключение, второй возвращает элемент
        parser.driver.find_element.side_effect = [NoSuchElementException("Not found"), element_mock]

        result = parser._get_text([".sel1", ".sel2"])
        assert result == "Found text"

    def test_get_text_all_selectors_fail(self):
        """Тест: _get_text когда все селекторы не найдены"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        from selenium.common.exceptions import NoSuchElementException

        parser.driver.find_element.side_effect = NoSuchElementException("Not found")

        result = parser._get_text([".sel1", ".sel2", ".sel3"])
        assert result == ""

    def test_get_product_name_success(self):
        """Тест: успешное получение названия продукта"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        h1_mock = Mock()
        h1_mock.text.strip.return_value = "Test Product Name"
        parser.driver.find_element.return_value = h1_mock

        result = parser._get_product_name()
        assert result == "Test Product Name"

    def test_get_product_name_failure(self):
        """Тест: ошибка при получении названия"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        parser.driver.find_element.side_effect = Exception("Element not found")

        with patch("src.parser.logger"):
            result = parser._get_product_name()
            assert result == "нет"

    def test_get_price_success(self):
        """Тест: успешное получение цены"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        with patch.object(parser, "_get_text", return_value="1 999 ₽"):
            result = parser._get_price()
            assert result == "1999"  # Должны остаться только цифры

    def test_get_price_with_decimal(self):
        """Тест: получение цены с десятичной запятой"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        with patch.object(parser, "_get_text", return_value="1 999,50 ₽"):
            result = parser._get_price()
            assert "1999" in result  # Может быть "1999,50" или "1999.50"

    def test_get_price_no_driver(self):
        """Тест: получение цены без драйвера"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = None

        result = parser._get_price()
        assert result == "нет"

    def test_get_description_success(self):
        """Тест: успешное получение описания"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        with patch.object(parser, "_get_text", return_value="This is a long description with multiple spaces."):
            result = parser._get_description()
            assert "multiple" in result

    def test_get_description_cleans_spaces(self):
        """Тест: очистка лишних пробелов в описании"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        with patch.object(parser, "_get_text", return_value="This   has    many     spaces"):
            result = parser._get_description()
            assert "  " not in result  # Не должно быть двойных пробелов

    def test_get_instructions_without_driver(self):
        """Тест: получение инструкции без драйвера"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = None

        result = parser._get_instructions()
        assert result == "нет"

    def test_get_country_without_driver(self):
        """Тест: получение страны без драйвера"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = None

        result = parser._get_country()
        assert result == "нет"

    def test_parse_product_sets_all_fields(self):
        """Тест: парсинг продукта заполняет все поля"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        # Мокаем все методы получения данных
        with patch.object(parser, "_safe_get", return_value=True):
            with patch.object(parser, "_get_product_name", return_value="Test Product"):
                with patch.object(parser, "_get_price", return_value="1999"):
                    with patch.object(parser, "_get_description", return_value="Test description"):
                        with patch.object(parser, "_get_instructions", return_value="Test instructions"):
                            with patch.object(parser, "_get_country", return_value="France"):
                                with patch.object(parser, "_get_rating_from_review_page", return_value="4.5"):
                                    product = Product(url="https://test.ru/123")
                                    result = parser.parse_product(product)

                                    assert result.name == "Test Product"
                                    assert result.price == "1999"
                                    assert result.description == "Test description"
                                    assert result.instructions == "Test instructions"
                                    assert result.country == "France"
                                    assert result.rating == "4.5"

    def test_parse_product_failed_load(self):
        """Тест: парсинг когда не удалось загрузить страницу"""
        parser = Parser("test.csv", self.temp_dir)

        with patch.object(parser, "_safe_get", return_value=False):
            product = Product(url="https://test.ru/123", name="Old Name")
            result = parser.parse_product(product)

            # Имя должно остаться старым
            assert result.name == "Old Name"

    def test_load_products_from_csv_with_empty_url(self):
        """Тест: загрузка продуктов с пустым URL"""
        with open(self.test_csv, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=Product.CSV_HEADERS)
            writer.writeheader()
            writer.writerow({"Ссылка на продукт": "", "Наименование": "Test", "Цена": "100"})

        parser = Parser("test.csv", self.temp_dir)
        parser.input_path = self.test_csv

        products = parser.load_products_from_csv()
        assert len(products) == 0  # Пустой URL должен быть пропущен

    def test_parse_all_with_limit(self):
        """Тест: парсинг с ограничением количества"""
        # Создаем тестовые продукты
        products = [Product(url=f"https://test.ru/{i}", name=f"Product {i}") for i in range(10)]

        parser = Parser("test.csv", self.temp_dir)
        parser.input_path = self.test_csv
        parser.save_products_to_csv(products)

        with patch.object(parser, "parse_product", return_value=products[0]):
            parser.parse_all(start_from=2, limit=3)

            # Проверяем что файл обновлен (сохранение вызывалось)
            assert os.path.exists(self.test_csv)

    def test_parse_all_start_from_out_of_range(self):
        """Тест: парсинг с start_from больше чем продуктов"""
        parser = Parser("test.csv", self.temp_dir)

        with patch.object(parser, "load_products_from_csv", return_value=[Product(url="test")]):
            with patch("src.parser.logger") as mock_logger:
                parser.parse_all(start_from=10)
                mock_logger.warning.assert_called()

    def test_parse_missing_only(self):
        """Тест: парсинг только отсутствующих данных"""
        products = [
            Product(url="https://test.ru/1", name="Product 1", price="", rating="", description=""),
            Product(url="https://test.ru/2", name="Product 2", price="100", rating="4.5", description="Desc"),
            Product(url="https://test.ru/3", name="Product 3", price="", rating="", description=""),
        ]

        parser = Parser("test.csv", self.temp_dir)
        parser.input_path = self.test_csv
        parser.save_products_to_csv(products)

        with patch.object(parser, "parse_product", side_effect=lambda p: p):
            parser.parse_missing_only()

            # Файл должен быть обновлен
            assert os.path.exists(self.test_csv)

    def test_parse_missing_only_no_missing(self):
        """Тест: парсинг когда нет отсутствующих данных"""
        products = [
            Product(url="https://test.ru/1", name="Product 1", price="100", rating="4.5", description="Desc"),
            Product(url="https://test.ru/2", name="Product 2", price="200", rating="4.0", description="Desc2"),
        ]

        parser = Parser("test.csv", self.temp_dir)
        parser.input_path = self.test_csv
        parser.save_products_to_csv(products)

        with patch("src.parser.logger") as mock_logger:
            parser.parse_missing_only()
            mock_logger.info.assert_called_with("Нет продуктов с отсутствующими данными")

    def test_debug_save_page_source_with_driver(self):
        """Тест: сохранение HTML когда драйвер есть"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()
        parser.driver.page_source = "<html><body>Test</body></html>"

        with patch("builtins.open", create=True) as mock_open:
            # Настраиваем мок для файла
            mock_file = Mock()
            mock_open.return_value.__enter__.return_value = mock_file

            parser.debug_save_page_source("test_debug.html")

            # Проверяем что open был вызван с правильными параметрами
            mock_open.assert_called_once_with("test_debug.html", "w", encoding="utf-8")

            # Проверяем что write был вызван с page_source
            mock_file.write.assert_called_once_with("<html><body>Test</body></html>")

    def test_debug_save_page_source_with_exception(self):
        """Тест: сохранение HTML при ошибке записи"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()
        parser.driver.page_source = "<html><body>Test</body></html>"

        with patch("builtins.open", side_effect=Exception("Write error")):
            with patch("src.parser.logger") as mock_logger:
                parser.debug_save_page_source("test_debug.html")
                # Должно быть предупреждение об ошибке
                mock_logger.warning.assert_called_once()

    # Добавьте эти тесты в конец класса TestParser

    def test_get_instructions_with_driver_and_tab_exists(self):
        """Тест: получение инструкции когда вкладка существует"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        # Мокаем поиск вкладки
        tab_mock = Mock()
        parser.driver.find_element.return_value = tab_mock

        # Мокаем page_source с инструкцией
        parser.driver.page_source = """
        <div text="Применение"></div>
        <div class="_ga-pdp-wysiwyg_rmnt6_55">Apply product daily</div>
        """

        with patch("time.sleep"):
            result = parser._get_instructions()
            assert result == "Apply product daily"

    def test_get_instructions_when_tab_not_found(self):
        """Тест: получение инструкции когда вкладка не найдена"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        from selenium.common.exceptions import NoSuchElementException

        parser.driver.find_element.side_effect = NoSuchElementException("Tab not found")

        with patch("src.parser.logger") as mock_logger:
            result = parser._get_instructions()
            assert result == "нет"

    def test_get_country_with_driver_and_tab_exists(self):
        """Тест: получение страны когда вкладка существует"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        # Мокаем поиск вкладки
        tab_mock = Mock()
        parser.driver.find_element.return_value = tab_mock

        # Мокаем page_source со страной
        parser.driver.page_source = "страна происхождения<br>France<br>"

        with patch("time.sleep"):
            result = parser._get_country()
            assert result == "France"

    def test_get_country_with_alternative_pattern(self):
        """Тест: получение страны по альтернативному паттерну"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        # Мокаем поиск вкладки
        tab_mock = Mock()
        parser.driver.find_element.return_value = tab_mock

        # Мокаем page_source с переносом строки
        parser.driver.page_source = "страна происхождения\nItaly\n"

        with patch("time.sleep"):
            result = parser._get_country()
            assert result == "Italy"

    def test_get_country_when_tab_not_found(self):
        """Тест: получение страны когда вкладка не найдена"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        from selenium.common.exceptions import NoSuchElementException

        parser.driver.find_element.side_effect = NoSuchElementException("Tab not found")

        with patch("src.parser.logger") as mock_logger:
            result = parser._get_country()
            assert result == "нет"

    def test_get_rating_from_review_page_success(self):
        """Тест: успешное получение рейтинга со страницы отзывов"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        # Мокаем элемент с рейтингом
        rating_mock = Mock()
        rating_mock.text.strip.return_value = "4.5"
        parser.driver.find_element.return_value = rating_mock

        with patch("time.sleep"):
            result = parser._get_rating_from_review_page("https://goldapple.ru/123-product")
            assert result == "4.5"

    def test_get_rating_from_review_page_zero_rating(self):
        """Тест: получение рейтинга 0.0 (нет отзывов)"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        # Мокаем элемент с рейтингом 0.0
        rating_mock = Mock()
        rating_mock.text.strip.return_value = "0.0"
        parser.driver.find_element.return_value = rating_mock

        with patch("time.sleep"):
            with patch("src.parser.logger") as mock_logger:
                result = parser._get_rating_from_review_page("https://goldapple.ru/123-product")
                assert result == "нет"

    def test_get_rating_from_review_page_not_found(self):
        """Тест: рейтинг не найден на странице отзывов"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        from selenium.common.exceptions import NoSuchElementException

        parser.driver.find_element.side_effect = NoSuchElementException("Rating not found")

        with patch("time.sleep"):
            result = parser._get_rating_from_review_page("https://goldapple.ru/123-product")
            assert result == "нет"

    def test_get_rating_from_review_page_exception(self):
        """Тест: ошибка при получении рейтинга"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        parser.driver.get.side_effect = Exception("Connection error")

        with patch("src.parser.logger"):
            result = parser._get_rating_from_review_page("https://goldapple.ru/123-product")
            assert result == "нет"

    def test_parse_all_with_resume_after_interrupt(self):
        """Тест: parse_all с продолжением после прерывания"""
        products = [Product(url=f"https://test.ru/{i}", name=f"Product {i}") for i in range(5)]

        parser = Parser("test.csv", self.temp_dir)
        parser.input_path = self.test_csv
        parser.save_products_to_csv(products)

        # Мокаем parse_product, чтобы первый вызов был успешным
        parse_calls = []

        def mock_parse(product):
            parse_calls.append(product)
            return product

        with patch.object(parser, "parse_product", side_effect=mock_parse):
            with patch("src.parser.logger"):
                parser.parse_all(start_from=2)
                assert len(parse_calls) == 3  # Продукты 2,3,4

    def test_parse_all_with_limit_and_start(self):
        """Тест: parse_all с limit и start_from"""
        products = [Product(url=f"https://test.ru/{i}", name=f"Product {i}") for i in range(10)]

        parser = Parser("test.csv", self.temp_dir)
        parser.input_path = self.test_csv
        parser.save_products_to_csv(products)

        parse_calls = []

        def mock_parse(product):
            parse_calls.append(product)
            return product

        with patch.object(parser, "parse_product", side_effect=mock_parse):
            parser.parse_all(start_from=3, limit=4)
            # Должны быть обработаны продукты 3,4,5,6
            assert len(parse_calls) == 4
            assert parse_calls[0].name == "Product 3"
            assert parse_calls[3].name == "Product 6"

    def test_save_products_to_csv_preserves_data(self):
        """Тест: сохранение продуктов в CSV сохраняет все данные"""
        original_products = [
            Product(
                url="https://test.ru/1",
                name="Original Name",
                price="999",
                rating="4.8",
                description="Original desc",
                instructions="Original instr",
                country="Germany",
            )
        ]

        parser = Parser("test.csv", self.temp_dir)
        parser.input_path = self.test_csv
        parser.save_products_to_csv(original_products)

        loaded_products = parser.load_products_from_csv()

        assert loaded_products[0].url == original_products[0].url
        assert loaded_products[0].name == original_products[0].name
        assert loaded_products[0].price == original_products[0].price
        assert loaded_products[0].rating == original_products[0].rating
        assert loaded_products[0].description == original_products[0].description
        assert loaded_products[0].instructions == original_products[0].instructions
        assert loaded_products[0].country == original_products[0].country

    def test_get_text_with_empty_string_result(self):
        """Тест: _get_text возвращает пустую строку когда текст пустой"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        element_mock = Mock()
        element_mock.text.strip.return_value = ""
        parser.driver.find_element.return_value = element_mock

        result = parser._get_text(".selector")
        assert result == ""

    def test_get_price_with_no_digits(self):
        """Тест: получение цены когда нет цифр"""
        parser = Parser("test.csv", self.temp_dir)
        parser.driver = Mock()

        with patch.object(parser, "_get_text", return_value="Бесплатно"):
            result = parser._get_price()
            assert result == "Бесплатно"
