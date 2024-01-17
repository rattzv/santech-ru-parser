import json
import os
import sqlite3

from utils.utils import print_template

FILENAME = "santech-ru"


def remove_old_data(reports_folder, cities):
    for city in cities:
        report_file_sqlite = os.path.join(reports_folder, 'sqlite', f'{city}-{FILENAME}.sqlite')
        report_file_json = os.path.join(reports_folder, 'sqlite', f'{city}-{FILENAME}.json')
        report_file_all_json = os.path.join(reports_folder, 'products.json')
        try:
            if os.path.exists(report_file_sqlite):
                print(print_template(f"Remove old data {report_file_sqlite}..."))
                os.remove(report_file_sqlite)
            if os.path.exists(report_file_json):
                print(print_template(f"Remove old data {report_file_json}..."))
                os.remove(report_file_json)
            if os.path.exists(report_file_all_json):
                print(print_template(f"Remove old data {report_file_all_json}..."))
                os.remove(report_file_all_json)
        except:
            print(print_template(f"Error when deleting old file"))


def save_to_sqlite(datetime_filename, products, reports_folder):
    try:
        report_file = os.path.join(reports_folder, 'sqlite', datetime_filename + FILENAME)

        conn = sqlite3.connect(report_file + ".sqlite")
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS json_data (id INTEGER PRIMARY KEY, data TEXT)''')

        for product in products:
            try:
                data = json.dumps(product, ensure_ascii=False, indent=4)
                cursor.execute("INSERT INTO json_data (data) VALUES (?)", (data,))
            except:
                continue
        conn.commit()
    except:
        return False


def convert_to_json(reports_folder, cities):
    total = []
    for city in cities:
        try:
            sqlite_report_file = os.path.join(reports_folder, 'sqlite', f'{city}-{FILENAME}.sqlite')
            if not os.path.exists(sqlite_report_file):
                continue

            json_report_file = os.path.join(reports_folder, 'json', f'{city}-{FILENAME}.json')

            conn = sqlite3.connect(sqlite_report_file)
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM json_data")
            rows = cursor.fetchall()
            conn.close()

            data_list = []
            for row in rows:
                try:
                    data_list.append(json.loads(row[0]))
                except:
                    continue

            total += data_list

            print(print_template(f"Convert to json {sqlite_report_file}..."))

            with open(json_report_file, 'w', encoding="utf-8") as file:
                json.dump(data_list, file, ensure_ascii=False, indent=4)
        except:
            continue

    total_report_file = os.path.join(reports_folder, 'products.json')
    with open(total_report_file, 'w', encoding="utf-8") as file:
        json.dump(total, file, ensure_ascii=False, indent=4)
    return len(total)




