class Product:
    def __init__(self, url, name, price, rating, description, instructions, country):
        self.url = url
        self.name = name
        self.price = price
        self.rating = rating
        self.description = description
        self.instructions = instructions
        self.country = country

    # для экспорта данных
    def to_dict(self):
        return {
            "Ссылка на продукт": self.url,
            "Наименование": self.name,
            "Цена": self.price,
            "Рейтинг пользователей": self.rating,
            "Описание продукта": self.description,
            "Инструкция по применению": self.instructions,
            "Страна-производитель": self.country
        }

    # для отчётов и логов
    def __str__(self):
        return (f"Ссылка на продукт: {self.url}\n"
                f"Наименование: {self.name}\n"
                f"Цена: {self.price}\n"
                f"Рейтинг пользователей: {self.rating}\n"
                f"Описание продукта: {self.description}\n"
                f"Инструкция по применению: {self.instructions}\n"
                f"Страна-производитель: {self.country}")

    # для отладки и разработки
    def __repr__(self):
        return (f"Product(url='{self.url}', "
                f"name='{self.name}', "
                f"price='{self.price}', "
                f"rating='{self.rating}', "
                f"description='{self.description}', "
                f"instructions='{self.instructions}', "
                f"country='{self.country}')")
