import time
from typing import Any, Dict, List

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
