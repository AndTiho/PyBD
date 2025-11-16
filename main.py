from config import config
from src.class_for_bd import DBManager
from src.create_add_to_bd import create_database, save_data_to_database
from src.work_with_api import get_hh_data


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
    create_database("hh_data", params)
    save_data_to_database(data, "hh_data", params)

    # Инициализация
    db = DBManager("hh_data", **params)

    print("Вас приветствует программа работы с вакансиями\nВыберете действие:")
    user_input = input(
        """
    1.Перечень всех компаний и кол-во вакансий
    2.Перечень всех вакансий
    3.Средняя зарплата
    4.Перечень вакансий c З/П выше среднего по таблице
    5.Вакансии с искомым словом
    """
    )
    # Получение данных
    if user_input == "1":
        companies = db.get_companies_and_vacancies_count()
        print("Перечень всех компаний и кол-во вакансий:")
        for row in companies:
            company, number = row
            print(f"Компания: {company}")
            print(f"Количество вакансий: {number}")
            print("-" * 50)  # разделитель между вакансиями

    elif user_input == "2":
        all_vacancies = db.get_all_vacancies()
        print("Перечень всех вакансий")
        for row in all_vacancies:
            company, job, salary_from, salary_to, currency, url = row
            print(f"Компания: {company}")
            print(f"Вакансия: {job}")
            print(f"Зарплата: {salary_from} – {salary_to} {currency or 'не указана'}")
            print(f"Ссылка: {url or 'нет ссылки'}")
            print("-" * 50)  # разделитель между вакансиями

    elif user_input == "3":
        avg_salary = db.get_avg_salary()
        print(f"Средняя зарплата: {round(avg_salary, 2)}\n")

    elif user_input == "4":
        high_salary_vacancies = db.get_vacancies_with_higher_salary()
        print("Перечень вакансий c З/П выше среднего по таблице")
        for row in high_salary_vacancies:
            company, job, salary_from, salary_to, currency, url = row
            print(f"Компания: {company}")
            print(f"Вакансия: {job}")
            print(f"Зарплата: {salary_from} – {salary_to} {currency or 'не указана'}")
            print(f"Ссылка: {url or 'нет ссылки'}")
            print("-" * 50)  # разделитель между вакансиями

    elif user_input == "5":
        keyword = input('Введите искомое слово( рекомендуем "продажам" ): ')
        python_vacancies = db.get_vacancies_with_keyword(keyword)
        print("Вакансии с искомым словом:")
        for row in python_vacancies:
            company, job, salary_from, salary_to, currency, url = row
            print(f"Компания: {company}")
            print(f"Вакансия: {job}")
            print(f"Зарплата: {salary_from} – {salary_to} {currency or 'не указана'}")
            print(f"Ссылка: {url or 'нет ссылки'}")
            print("-" * 50)  # разделитель между вакансиями
    else:
        print("Ошибка ввода, закрытие программы.")

    # Закрытие соединения
    db.close()


if __name__ == "__main__":
    main()
