import json
from typing import List, Dict, Any
from config.config import EXCELL_TOKEN
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class ExcellLoader:
    def __init__(self, EXCELL_TOKEN):
        # Настройка подключения к Google Sheets
        self.SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        self.CREDENTIALS_FILE = "../config/engineergps.json"  # JSON-файл с ключами сервисного аккаунта
        self.SPREADSHEET_ID = EXCELL_TOKEN  # ID таблицы Google Sheets (находится в URL)
        # (часть URL таблицы между /d/ и /edit), а не названием таблицы.

    # Подключение к таблице Google Sheets
    def connect_to_google_sheet(self):
        scope = self.SCOPE
        credentials = ServiceAccountCredentials.from_json_keyfile_name(self.CREDENTIALS_FILE, scope)
        client = gspread.authorize(credentials)
        return client.open_by_key(self.SPREADSHEET_ID)

    # Чтение данных из таблицы
    def read_google_sheet(self):
        # sheet = connect_to_google_sheet().sheet1  # Відкриваємо перший лист
        sheet = self.connect_to_google_sheet().worksheet("База трекерів")  # Відкриваємо лист по назві

        data = sheet.get_all_values()  # Отримуємо всі дані
        return data

    def create_base_list(self) -> List[Dict[str, Any]]:
        """
        Створюэмо list з словником по кожному трекеру
        :return: lsit
        """
        # Генерация JSON
        result = []
        try:
            data = file_excel.read_google_sheet()

            headers = None
            for row in data:
                if any(row):  # Если строка не пустая
                    headers = row
                    break
            headers = [item for item in headers if item]

            for row in data:
                if any(row):  # Пропускаем пустые строки
                    if row != headers:  # Пропускаем строку с заголовками
                        result.append(dict(zip(headers, row)))

        except Exception as e:
            print(f"Ошибка: {e}")
        return result

    def find_emei(self, part_emei: str, json_list:List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Функція пошуку emei в List[Dict[str, Any]]
        :param part_emei: частина emei по якому будемо виконувати пошук
        :param json_list: лист з json де будемо шукати
        :return: повертаэ лист з знайденими json
        """

        if not part_emei.isdigit():
            return []
        search_list = []
        for item in json_list:
            if item["ИМЕИ"].endswith(part_emei) or item["ИМЕИ2"].endswith(part_emei):
                search_list.insert(0,item)
            elif part_emei in item["ИМЕИ"] or part_emei in item["ИМЕИ2"]:
                search_list.append(item)

        return search_list

# Пример использования
if __name__ == "__main__":

    file_excel = ExcellLoader(EXCELL_TOKEN)
    json_list = file_excel.create_base_list()
    # Генерация JSON-строки
    #json_output = json.dumps(json_list, ensure_ascii=False, indent=4)
    #print(json_output)
    result = file_excel.find_emei("71525",json_list)
    print(json.dumps(result, ensure_ascii=False, indent=4))






