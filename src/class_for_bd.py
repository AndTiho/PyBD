from typing import List, Optional, Tuple

import psycopg2


class DBManager:
    def __init__(self, dbname: str, user: str, password: str, host: str = "localhost", port: int = 5432):
        """
        Инициализация подключения к БД PostgreSQL.

        :param dbname: название базы данных
        :param user: имя пользователя
        :param password: пароль
        :param host: хост (по умолчанию localhost)
        :param port: порт (по умолчанию 5432)
        """
        self.conn_params = {"dbname": dbname, "user": user, "password": password, "host": host, "port": port}
        self.conn = None

    def connect(self):
        """Устанавливает соединение с БД."""
        try:
            self.conn = psycopg2.connect(**self.conn_params)
        except psycopg2.Error as e:
            raise ConnectionError(f"Ошибка подключения к БД: {e}")

    def close(self):
        """Закрывает соединение с БД."""
        if self.conn:
            self.conn.close()

    def get_companies_and_vacancies_count(self) -> List[Tuple[str, int]]:
        """
        Получает список всех компаний и количество вакансий у каждой компании.

        :return: список кортежей (название_компании, количество_вакансий)
        """
        if not self.conn:
            self.connect()

        with self.conn.cursor() as cur:
            cur.execute(
                """
            SELECT
                e.name AS company_name,
                COUNT(v.vacancy_id) AS vacancies_count
            FROM employers e
            LEFT JOIN vacancies v ON e.employer_id = v.employer_id
            GROUP BY e.name
            ORDER BY vacancies_count DESC
            """
            )
            return cur.fetchall()

    def get_all_vacancies(self) -> List[Tuple[str, str, Optional[float], Optional[float], Optional[str], str]]:
        """
        Получает список всех вакансий с указанием:
        - названия компании,
        - названия вакансии,
        - зарплаты от,
        - зарплаты до,
        - валюты,
        - ссылки на вакансию (site_url из employers).

        :return: список кортежей (компания, вакансия, зарплата_от, зарплата_до, валюта, ссылка)
        """
        if not self.conn:
            self.connect()

        with self.conn.cursor() as cur:
            cur.execute(
                """
            SELECT
                e.name AS company_name,
                v.name AS vacancy_name,
                v.salary_from,
                v.salary_to,
                v.currency,
                e.site_url AS company_site
            FROM vacancies v
            JOIN employers e ON v.employer_id = e.employer_id
            ORDER BY v.vacancy_id
            """
            )
            return cur.fetchall()

    def get_avg_salary(self) -> float:
        """
        Получает среднюю зарплату по вакансиям (среднее от salary_from).
        Учитывает только записи, где salary_from НЕ NULL.

        :return: средняя зарплата (float), 0.0 если данных нет
        """
        if not self.conn:
            self.connect()

        with self.conn.cursor() as cur:
            cur.execute(
                """
            SELECT AVG(salary_from) FROM vacancies WHERE salary_from IS NOT NULL
            """
            )
            result = cur.fetchone()
            return float(result[0]) if result[0] is not None else 0.0

    def get_vacancies_with_higher_salary(self) -> List[Tuple]:
        """
        Получает список вакансий, у которых зарплата (salary_from) выше средней по всем вакансиям.

        :return: список кортежей с данными вакансий (компания, вакансия, зарплата_от, зарплата_до, валюта, ссылка)
        """
        if not self.conn:
            self.connect()

        avg_salary = self.get_avg_salary()

        with self.conn.cursor() as cur:
            cur.execute(
                """
            SELECT
                e.name AS company_name,
                v.name AS vacancy_name,
                v.salary_from,
                v.salary_to,
                v.currency,
                e.site_url AS company_site
            FROM vacancies v
            JOIN employers e ON v.employer_id = e.employer_id
            WHERE v.salary_from > %s
            ORDER BY v.salary_from DESC
            """,
                (avg_salary,),
            )
            return cur.fetchall()

    def get_vacancies_with_keyword(self, keyword: str) -> List[Tuple]:
        """
        Получает список вакансий, в названии которых содержится ключевое слово (без учёта регистра).

        :param keyword: ключевое слово для поиска (например, 'python')
        :return: список кортежей с данными вакансий (компания, вакансия, зарплата_от, зарплата_до, валюта, ссылка)
        """
        if not self.conn:
            self.connect()

        search_pattern = f"%{keyword}%"

        with self.conn.cursor() as cur:
            cur.execute(
                """
            SELECT
                e.name AS company_name,
                v.name AS vacancy_name,
                v.salary_from,
                v.salary_to,
                v.currency,
                e.site_url AS company_site
            FROM vacancies v
            JOIN employers e ON v.employer_id = e.employer_id
            WHERE LOWER(v.name) LIKE LOWER(%s)
            ORDER BY v.vacancy_id
            """,
                (search_pattern,),
            )
            return cur.fetchall()
