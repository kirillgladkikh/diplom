import csv
# from .product import Product

class CSVExporter:
    def __init__(self, filename):
        self.filename = filename

    def export(self, products):
        with open(self.filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                "Ссылка на продукт",
                "Наименование",
                "Цена",
                "Рейтинг пользователей",
                "Описание продукта",
                "Инструкция по применению",
                "Страна-производитель"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for product in products:
                writer.writerow(product.to_dict())
        print(f"Данные успешно сохранены в {self.filename}")
