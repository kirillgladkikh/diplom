class Product:
    """Модель продукта - единый источник истины для структуры данных"""
    # Заголовки итогового CSV-файла (определены здесь, потому что это структура данных)
    CSV_HEADERS = [
        "Ссылка на продукт",
        "Наименование",
        "Цена",
        "Рейтинг пользователей",
        "Описание продукта",
        "Инструкция по применению",
        "Страна-производитель"
    ]

    def __init__(self, url=None, name=None, price=None, rating=None,
                 description=None, instructions=None, country=None):
        self.url = url
        self.name = name
        self.price = price
        self.rating = rating
        self.description = description
        self.instructions = instructions
        self.country = country

    def to_dict(self):
        """Конвертирует в словарь для CSV (порядок соответствует CSV_HEADERS)"""
        return {
            "Ссылка на продукт": self.url or "",
            "Наименование": self.name or "",
            "Цена": self.price or "",
            "Рейтинг пользователей": self.rating or "",
            "Описание продукта": self.description or "",
            "Инструкция по применению": self.instructions or "",
            "Страна-производитель": self.country or ""
        }
