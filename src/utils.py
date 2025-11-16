import time
from typing import Any, List, Dict

import psycopg2
import requests


def get_hh_data(employer_ids: List[str]) -> List[Dict[str, Any]]:
    """Получение данных о работодателях и их вакансиях с HH.ru"""

    data = []
    headers = {"User-Agent": "HH-User-Agent"}

    for employer_id in employer_ids:
        # 1. Получаем данные о работодателе
        employer_url = f"https://api.hh.ru/employers/{employer_id}"
        employer_response = requests.get(employer_url, headers=headers)

        if employer_response.status_code != 200:
            print(f"Ошибка при получении работодателя {employer_id}: {employer_response.status_code}")
            continue  # пропускаем и идём к следующему ID

        employer = employer_response.json()

        # 2. Получаем вакансии работодателя (с пагинацией)
        vacancies = []
        page = 0
        while True:
            vacancies_url = "https://api.hh.ru/vacancies"
            params = {"employer_id": employer_id, "page": page, "per_page": 100}  # максимум за запрос

            vacancies_response = requests.get(vacancies_url, headers=headers, params=params)

            if vacancies_response.status_code != 200:
                print(
                    f"Ошибка при получении вакансий {employer_id}, страница {page}: {vacancies_response.status_code}"
                )
                break

            response_data = vacancies_response.json()
            page_vacancies = response_data["items"]

            if not page_vacancies:  # больше нет страниц
                break

            vacancies.extend(page_vacancies)
            page += 1

            # Пауза между запросами (защита от блокировки)
            time.sleep(1)

        # 3. Объединяем данные работодателя и его вакансии
        data.append({"employer": employer, "vacancies": vacancies})

        # Пауза между работодателями
        time.sleep(1)

    return data


def create_database(database_name: str, params: dict):
    """Создание базы данных и таблиц для сохранения данных о работодателях и вакансиях"""

    conn = psycopg2.connect(dbname="postgres", **params)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute(f"DROP DATABASE IF EXISTS {database_name}")
    cur.execute(f"CREATE DATABASE {database_name} WITH ENCODING 'UTF8'")

    conn.close()

    conn = psycopg2.connect(dbname=database_name, **params)

    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS employers (
                employer_id VARCHAR(50) PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                site_url TEXT,
                area_name VARCHAR(100),
                active_vacancies INTEGER DEFAULT 0)
            """
        )

    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS vacancies (
                vacancy_id VARCHAR(50) PRIMARY KEY,
                employer_id VARCHAR(50) REFERENCES employers(employer_id) ON DELETE CASCADE,
                name VARCHAR(500) NOT NULL,
                salary_from NUMERIC(12, 2),
                salary_to NUMERIC(12, 2),
                currency VARCHAR(10),
                requirement TEXT,
                responsibility TEXT)
            """
        )

    conn.commit()
    conn.close()


def save_data_to_database(data: list[dict[str, Any]], database_name: str, params: dict):
    """Сохранение данных о работодателях и вакансиях в базу данных."""
    conn = psycopg2.connect(dbname=database_name, **params)

    with conn.cursor() as cur:
        for employer in data:
            employer_data = employer["employer"]
            employer_area = employer["employer"]["area"]

            cur.execute(
                """
                INSERT INTO employers (employer_id, name, description, site_url, area_name, active_vacancies)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING employer_id
                """,
                (
                    employer_data["id"],
                    employer_data["name"],
                    employer_data["description"],
                    employer_data["site_url"],
                    employer_area["name"],
                    employer_data["open_vacancies"]
                ),
            )

            employer_id = cur.fetchone()[0]
            vacancies_data = employer["vacancies"]

            for vacancy in vacancies_data:
                # Извлекаем зарплату с проверкой на None
                salary = vacancy["salary"]
                if salary is not None:
                    salary_from = salary["from"]
                    salary_to = salary["to"]
                    currency = salary["currency"]
                else:
                    salary_from = 0
                    salary_to = 0
                    currency = None

                # Извлекаем snippet с проверкой на None
                snippet = vacancy.get("snippet")
                if snippet is not None:
                    requirement = snippet.get("requirement")
                    responsibility = snippet.get("responsibility")  # responsibility проверьте написание ключа!
                else:
                    requirement = None
                    responsibility = None

                cur.execute(
                    """
                    INSERT INTO vacancies (vacancy_id, name, salary_from, salary_to, currency, requirement, responsibility)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        vacancy["id"],
                        vacancy["name"],
                        salary_from,
                        salary_to,
                        currency,
                        requirement,
                        responsibility
                    ),
                )

    conn.commit()
    conn.close()
