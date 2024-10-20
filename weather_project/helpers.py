import csv
import json

def load_country_codes(file_path):
    """
    Loads country codes and names from a CSV file into a dictionary.
    """
    country_dict = {}
    with open(file_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            country_dict[row['code']] = row['country']
    return country_dict

def load_city_data(file_path):
    """
    Loads city names and country codes from the cities500.txt file into a list.
    Expects the file to be tab-separated (TSV).
    """
    city_list = []
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='\t')
        for row in reader:
            # Index 1: City name, Index 8: Country code
            if len(row) >= 9:  # Ensure the row has the necessary columns
                city_name = row[1]
                country_code = row[8]
                city_list.append((city_name, country_code))
    return city_list


def get_city_suggestions(query, city_list, limit=5):
    """
    Suggests cities based on the input query.
    """
    query = query.lower()
    suggestions = [city for city in city_list if query in city.lower()]
    return suggestions[:limit]

def load_language(language_code):
    try:
        with open(f'translations/{language_code}.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Translation file for {language_code} not found. Defaulting to English.")
        with open('translations/en.json', 'r', encoding='utf-8') as f:
            return json.load(f)
