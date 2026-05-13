import os
import requests
import time

from dotenv import load_dotenv
from terminaltables import SingleTable


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    elif salary_from and not salary_to:
        return salary_from * 1.2
    elif not salary_from and salary_to:
        return salary_to * 0.8
    else:
        return None


def predict_rub_salary_habr(vacancy):
    salary = vacancy.get('salary')

    if salary and (salary.get('from') is not None or salary.get('to') is not None):
        pass

    else:
        salary = vacancy.get('predictedSalary')

    if not salary:
        return None

    salary_from = salary.get('from')
    salary_to = salary.get('to')
    currency = salary.get('currency')

    if currency != 'rur':
        return None
    return predict_salary(salary_from, salary_to)


def sort_habr_vacancies_by_language(language):
    url = 'https://career.habr.com/api/frontend/vacancies'
    sorted_vacancies = []
    page = 1
    total_pages = 1
    vacancies_found = 0

    while page <= total_pages:
        params = {'q': language, 'city_id': '678', 'page': page}  # city_id 678 - Moscow
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if page == 1:
            total_pages = data.get('meta', {}).get('totalPages', 1)
            vacancies_found = data.get('meta', {}).get('totalResults', 0)

        sorted_vacancies.extend(data.get('list', []))
        page += 1
        time.sleep(0.2)

    return sorted_vacancies, vacancies_found


def get_habr_stats(language):
    sorted_vacancies, vacancies_found = sort_habr_vacancies_by_language(language)
    salaries = []

    for vacancy in sorted_vacancies[:min(100, len(sorted_vacancies))]:
        salary = predict_rub_salary_habr(vacancy)
        if salary:
            salaries.append(salary)
        time.sleep(0.2)

    vacancies_processed = len(salaries)
    average_salary = int(sum(salaries) / len(salaries)) if salaries else None

    return {
        'vacancies_found': vacancies_found,
        'vacancies_processed': vacancies_processed,
        'average_salary': average_salary
    }


def predict_rub_salary_sjob(vacancy):
    payment_from = vacancy.get('payment_from')
    payment_to = vacancy.get('payment_to')
    return predict_salary(payment_from, payment_to)


def get_sjob_stats(sjob_api_key, language):
    url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {
        'X-Api-App-Id': sjob_api_key
    }
    vacancies_found = 0
    salaries = []
    page = 0

    while True:
        params = {
            'keyword': language,
            'town': '4',  # Moscow
            'count': 20,
            'page': page
        }

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        if page == 0:
            vacancies_found = data.get('total', 0)

        for vacancy in data.get('objects', []):
            salary = predict_rub_salary_sjob(vacancy)
            if salary:
                salaries.append(salary)

        if not data.get('more'):
            break

        page += 1
        time.sleep(0.2)

    vacancies_processed = len(salaries)
    average_salary = int(sum(salaries) / len(salaries)) if salaries else None

    return {
        'vacancies_found': vacancies_found,
        'vacancies_processed': vacancies_processed,
        'average_salary': average_salary
    }


def create_table(title, data):
    table_data = [
        ['Язык программирования', 'Вакансий найдено', 'Вакансий обработано ', 'Средняя зарплата']
    ]

    for language, stats in data.items():
        table_data.append([
            language,
            str(stats['vacancies_found']),
            str(stats['vacancies_processed']),
            str(stats['average_salary'] or 'n/a')
        ])

    table = SingleTable(table_data, title)
    print(table.table)


def main():

    load_dotenv()

    sjob_api_key = os.environ['SJOB_SECRET_KEY']

    languages = [
        'Python',
        'Java',
        'JavaScript',
        'Ruby',
        'PHP',
        'C++',
        'C#',
    ]

    habr_stats = {language: get_habr_stats(language) for language in languages}
    sjob_stats = {language: get_sjob_stats(sjob_api_key, language) for language in languages}
    create_table("Habr Moscow", habr_stats)
    create_table("SuperJob Moscow", sjob_stats)


if __name__ == '__main__':
    main()
