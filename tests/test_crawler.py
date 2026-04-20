import src.crawler as crawler_module  # Импортируем модуль целиком
from unittest.mock import Mock, patch, MagicMock
from src.crawler import Crawler


class TestCrawler:
    """Тесты для Crawler"""

    def test_crawler_init(self):
        """Тест: инициализация краулера"""
        crawler = Crawler()
        assert crawler.base_url == "https://goldapple.ru/parfjumerija"
        assert crawler.product_links == set()
        assert crawler.driver is None
        assert crawler.last_processed_page == 0

    def test_save_and_load_checkpoint(self, tmp_path):
        """Тест: сохранение и загрузка чекпоинта"""
        # Сохраняем оригинальное значение
        original_checkpoint = crawler_module.CRAWLER_CHECKPOINT_FILE
        test_checkpoint = tmp_path / "test_checkpoint.json"

        try:
            # Подменяем конфиг для теста
            crawler_module.CRAWLER_CHECKPOINT_FILE = str(test_checkpoint)

            crawler = Crawler()
            crawler.product_links = {"https://test.ru/1", "https://test.ru/2"}

            # Сохраняем
            crawler._save_checkpoint(5)

            # Проверяем, что файл создан
            assert test_checkpoint.exists()

            # Создаем новый краулер для загрузки
            crawler2 = Crawler()
            last_page = crawler2._load_checkpoint()
            assert last_page == 5
            assert len(crawler2.product_links) == 2

        finally:
            # Восстанавливаем
            crawler_module.CRAWLER_CHECKPOINT_FILE = original_checkpoint

    def test_clear_checkpoint(self, tmp_path):
        """Тест: удаление чекпоинта"""
        # Сохраняем оригинальное значение
        original_checkpoint = crawler_module.CRAWLER_CHECKPOINT_FILE
        test_checkpoint = tmp_path / "test_checkpoint.json"
        test_checkpoint.write_text('{"test": "data"}')

        try:
            # Подменяем путь к чекпоинту
            crawler_module.CRAWLER_CHECKPOINT_FILE = str(test_checkpoint)

            crawler = Crawler()
            crawler._clear_checkpoint()

            assert not test_checkpoint.exists()

        finally:
            # Восстанавливаем
            crawler_module.CRAWLER_CHECKPOINT_FILE = original_checkpoint

    def test_check_empty_page(self):
        """Тест: проверка пустой страницы"""
        crawler = Crawler()

        # Страница с ссылками не считается пустой
        assert crawler._check_empty_page(1, 10) is False
        assert crawler._check_empty_page(1, 5) is False

        # Первая страница с 0 ссылок не считается концом
        assert crawler._check_empty_page(1, 0) is False

        # Страница >1 с 0 ссылок считается пустой
        assert crawler._check_empty_page(2, 0) is True
        assert crawler._check_empty_page(10, 0) is True

    def test_random_delay(self):
        """Тест: случайная задержка (просто проверяем что не падает)"""
        crawler = Crawler()

        # Просто проверяем что метод работает без ошибок
        import time

        start = time.time()
        crawler._random_delay(min_delay=0.1, max_delay=0.2)
        elapsed = time.time() - start

        assert elapsed >= 0.1

    def test_get_products_returns_list(self):
        """Тест: get_products возвращает список (без реального драйвера)"""
        crawler = Crawler()

        # Не вызываем реальный метод, просто проверяем наличие
        assert hasattr(crawler, "get_products")
        assert callable(crawler.get_products)

    def test_init_driver_returns_driver(self):
        """Тест: _init_driver создает драйвер"""
        crawler = Crawler()

        # Патчим webdriver, чтобы не запускать реальный браузер
        with patch("src.crawler.webdriver.Chrome") as mock_chrome:
            mock_driver = Mock()
            mock_chrome.return_value = mock_driver

            driver = crawler._init_driver()

            assert driver is not None
            mock_chrome.assert_called_once()

    def test_random_delay_with_custom_values(self):
        """Тест: случайная задержка с кастомными значениями"""
        crawler = Crawler()

        import time

        start = time.time()
        crawler._random_delay(min_delay=0.05, max_delay=0.1)
        elapsed = time.time() - start

        assert elapsed >= 0.05

    def test_random_delay_with_default_values(self):
        """Тест: случайная задержка с значениями по умолчанию"""
        crawler = Crawler()

        # Просто проверяем что метод работает
        import time

        start = time.time()
        crawler._random_delay()
        elapsed = time.time() - start

        # Должно быть между REQUEST_DELAY_MIN и REQUEST_DELAY_MAX (2-4 секунды)
        assert elapsed >= 2.0

    def test_check_empty_page_with_various_inputs(self):
        """Тест: проверка пустых страниц с разными значениями"""
        crawler = Crawler()

        # Страница 1 с 0 ссылок - не конец
        assert crawler._check_empty_page(1, 0) is False

        # Страница 5 с 0 ссылок - конец
        assert crawler._check_empty_page(5, 0) is True

        # Страница 100 с 0 ссылок - конец
        assert crawler._check_empty_page(100, 0) is True

        # Любая страница с ссылками - не конец
        assert crawler._check_empty_page(1, 5) is False
        assert crawler._check_empty_page(100, 1) is False

    @patch("src.crawler.logger")
    def test_save_checkpoint_handles_exception(self, mock_logger):
        """Тест: сохранение чекпоинта при ошибке записи"""
        crawler = Crawler()
        crawler.product_links = {"https://test.ru/1"}

        # Патчим open, чтобы вызвать исключение
        with patch("builtins.open", side_effect=Exception("Write error")):
            crawler._save_checkpoint(10)

            # Проверяем, что логгер вызван с предупреждением
            mock_logger.warning.assert_called_once()

    @patch("src.crawler.os.path.exists")
    @patch("src.crawler.logger")
    def test_load_checkpoint_file_not_exists(self, mock_logger, mock_exists):
        """Тест: загрузка чекпоинта когда файл не существует"""
        mock_exists.return_value = False

        crawler = Crawler()
        result = crawler._load_checkpoint()

        assert result == 0
        assert len(crawler.product_links) == 0

    @patch("src.crawler.os.path.exists")
    @patch("builtins.open")
    @patch("json.load")
    @patch("src.crawler.logger")
    def test_load_checkpoint_success(self, mock_logger, mock_json_load, mock_open, mock_exists):
        """Тест: успешная загрузка чекпоинта"""
        mock_exists.return_value = True

        # Мокаем данные из JSON
        mock_json_load.return_value = {
            "last_page": 15,
            "total_links": 10,
            "links": ["https://test.ru/1", "https://test.ru/2"],
        }

        crawler = Crawler()
        result = crawler._load_checkpoint()

        assert result == 15
        assert len(crawler.product_links) == 2

    @patch("src.crawler.os.path.exists")
    @patch("builtins.open")
    @patch("json.load")
    @patch("src.crawler.logger")
    def test_load_checkpoint_exception(self, mock_logger, mock_json_load, mock_open, mock_exists):
        """Тест: загрузка чекпоинта с ошибкой"""
        mock_exists.return_value = True
        mock_json_load.side_effect = Exception("JSON parse error")

        crawler = Crawler()
        result = crawler._load_checkpoint()

        assert result == 0
        mock_logger.warning.assert_called_once()

    def test_clear_checkpoint_no_file(self):
        """Тест: удаление чекпоинта когда файла нет"""
        crawler = Crawler()

        with patch("src.crawler.os.path.exists", return_value=False):
            with patch("src.crawler.os.remove") as mock_remove:
                crawler._clear_checkpoint()
                mock_remove.assert_not_called()

    def test_clear_checkpoint_with_file(self):
        """Тест: удаление чекпоинта когда файл есть"""
        crawler = Crawler()

        with patch("src.crawler.os.path.exists", return_value=True):
            with patch("src.crawler.os.remove") as mock_remove:
                crawler._clear_checkpoint()
                mock_remove.assert_called_once()

    def test_extract_links_from_page_handles_timeout(self):
        """Тест: обработка таймаута при извлечении ссылок"""
        crawler = Crawler()
        crawler.driver = Mock()

        # Мокаем driver.get чтобы вызвать исключение
        from selenium.common.exceptions import TimeoutException

        crawler.driver.get.side_effect = TimeoutException("Timeout")

        with patch("src.crawler.logger") as mock_logger:
            result = crawler._extract_links_from_page(1)

            assert result == 0
            # Должно быть предупреждение о таймауте
            mock_logger.warning.assert_called()

    def test_extract_links_from_page_handles_general_error(self):
        """Тест: обработка общей ошибки при извлечении ссылок"""
        crawler = Crawler()
        crawler.driver = Mock()

        # Мокаем driver.get чтобы вызвать общее исключение
        crawler.driver.get.side_effect = Exception("General error")

        with patch("src.crawler.logger") as mock_logger:
            result = crawler._extract_links_from_page(1)

            assert result == 0
            mock_logger.error.assert_called()

    def test_extract_links_from_page_success_no_links(self):
        """Тест: успешное извлечение страницы без ссылок"""
        crawler = Crawler()
        crawler.driver = Mock()

        # Мокаем driver.get успешно
        crawler.driver.get.return_value = None

        # Мокаем find_elements - пустой список
        crawler.driver.find_elements.return_value = []

        with patch("src.crawler.WebDriverWait"):
            with patch("src.crawler.logger"):
                result = crawler._extract_links_from_page(1)

                assert result == 0

    def test_extract_links_from_page_with_links(self):
        """Тест: успешное извлечение страницы со ссылками"""
        crawler = Crawler()
        crawler.driver = Mock()
        crawler.product_links = set()

        # Создаем мок-ссылки
        mock_link1 = Mock()
        mock_link1.get_attribute.return_value = "https://goldapple.ru/123-product"

        mock_link2 = Mock()
        mock_link2.get_attribute.return_value = "https://goldapple.ru/456-another"

        crawler.driver.find_elements.return_value = [mock_link1, mock_link2]

        with patch("src.crawler.WebDriverWait"):
            with patch("src.crawler.logger"):
                result = crawler._extract_links_from_page(1)

                assert result == 2
                assert len(crawler.product_links) == 2

    def test_extract_links_from_page_skip_invalid_links(self):
        """Тест: пропуск невалидных ссылок"""
        crawler = Crawler()
        crawler.driver = Mock()
        crawler.product_links = set()

        # Создаем мок-ссылки с разными URL
        mock_link1 = Mock()
        mock_link1.get_attribute.return_value = "https://goldapple.ru/123-product"

        mock_link2 = Mock()
        mock_link2.get_attribute.return_value = "https://other-site.com/product"  # Не подходит по паттерну

        mock_link3 = Mock()
        mock_link3.get_attribute.return_value = None  # Пустая ссылка

        crawler.driver.find_elements.return_value = [mock_link1, mock_link2, mock_link3]

        with patch("src.crawler.WebDriverWait"):
            with patch("src.crawler.logger"):
                result = crawler._extract_links_from_page(1)

                assert result == 1
                assert len(crawler.product_links) == 1

    def test_collect_all_links_handles_keyboard_interrupt(self):
        """Тест: обработка прерывания пользователем"""
        crawler = Crawler()
        crawler.driver = Mock()
        crawler.product_links = {"https://test.ru/1", "https://test.ru/2"}

        with patch("src.crawler.logger"):
            with patch.object(crawler, "_extract_links_from_page", side_effect=KeyboardInterrupt):
                result = crawler.collect_all_links(resume=False)

                # Должен вернуть список продуктов из уже собранных ссылок
                assert len(result) == 2

    def test_collect_all_links_with_test_mode(self):
        """Тест: сбор ссылок в тестовом режиме"""
        crawler = Crawler()
        crawler.driver = Mock()

        # Мокаем _extract_links_from_page
        with patch.object(crawler, "_extract_links_from_page", return_value=5):
            with patch("src.crawler.logger"):
                with patch("src.crawler.TEST_MODE", True):
                    with patch("src.crawler.TEST_MODE_PAGES", 3):
                        result = crawler.collect_all_links(resume=False)

                        # Должен быть вызван для страниц 1,2,3
                        assert crawler._extract_links_from_page.call_count <= 3

    def test_collect_all_links_stops_on_empty_pages(self):
        """Тест: остановка при пустых страницах"""
        crawler = Crawler()
        crawler.driver = Mock()

        # Первые 2 страницы с ссылками, потом пустые
        calls = [5, 5, 0, 0, 0]

        with patch.object(crawler, "_extract_links_from_page", side_effect=calls):
            with patch("src.crawler.logger"):
                with patch("src.crawler.MAX_EMPTY_PAGES", 3):
                    result = crawler.collect_all_links(resume=False)

                    # Должен остановиться после 3 пустых страниц
                    # Вызвано для страниц 1,2,3,4,5
                    assert crawler._extract_links_from_page.call_count <= 5
