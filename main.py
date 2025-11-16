import os

from src.utils import get_hh_data, create_database, save_data_to_database
from config import config


def main():
    employer_ids = [
        "4910000",  # ООО Евразия 2
        "1807902",  # ООО ИВА 2
        "9611595",  # ООО Кавара 2
        "2642865",  # ООО Лаборатория кофе 1
        "6168988",  # Магазин Pore Over 1
        "9418321",  # ООО Кабинет Врача 2
        "5483837",  # ООО НАВИ 1
        "4483835",  # Обелиск 0
        "11429244",  # Пакитан 4
        "10155127",  # ООО Я7 1
    ]

    params = config()

    data = get_hh_data(employer_ids)
    create_database('hh_data', params)
    save_data_to_database(data, 'hh_data', params)


if __name__ == "__main__":
    main()
