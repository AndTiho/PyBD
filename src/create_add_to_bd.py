from typing import Any

import psycopg2


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
                    employer_data["open_vacancies"],
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
                    INSERT INTO vacancies (vacancy_id, name, salary_from, salary_to, currency, requirement, responsibility, employer_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        vacancy["id"],
                        vacancy["name"],
                        salary_from,
                        salary_to,
                        currency,
                        requirement,
                        responsibility,
                        employer_id,
                    ),
                )

    conn.commit()
    conn.close()
