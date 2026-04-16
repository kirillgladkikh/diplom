import csv
import os
from src.product import Product


class CSVExporter:
    """Экспорт данных в CSV"""
    def __init__(self, filename, data_dir="data"):
        self.filename = filename
        self.data_dir = data_dir

        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

    def get_full_path(self):
        return os.path.join(self.data_dir, self.filename)

    def export(self, products):
        """Экспортирует список продуктов в CSV"""
        if not products:
            print("Нет данных для экспорта")
            return False

        full_path = self.get_full_path()

        with open(full_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            # Берём заголовки из класса Product (единый источник)
            writer = csv.DictWriter(csvfile, fieldnames=Product.CSV_HEADERS)
            writer.writeheader()

            for product in products:
                writer.writerow(product.to_dict())

        print(f"Данные успешно сохранены в {full_path}")
        print(f"Всего записей: {len(products)}")
        return True


# import csv
# # from .product import Product
#
# class CSVExporter:
#     def __init__(self, filename):
#         self.filename = filename
#
#     def export(self, products):
#         with open(self.filename, 'w', newline='', encoding='utf-8') as csvfile:
#             fieldnames = [
#                 "Ссылка на продукт",
#                 "Наименование",
#                 "Цена",
#                 "Рейтинг пользователей",
#                 "Описание продукта",
#                 "Инструкция по применению",
#                 "Страна-производитель"
#             ]
#             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
#             writer.writeheader()
#             for product in products:
#                 writer.writerow(product.to_dict())
#         print(f"Данные успешно сохранены в {self.filename}")
