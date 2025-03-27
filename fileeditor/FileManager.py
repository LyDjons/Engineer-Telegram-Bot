from idlelib.iomenu import encoding
import re
import chardet
import io
import os
import pandas as pd

class FileManager:

    def __init__(self, file_input, bot):
        """ конструктор класу приймає завантажений файл з боту
              :__file_input     - вхідний файл з бота
              :_chat_file       - інформація про тарувальну таблицю
              :__bot            - бот
              :__info           - інформація про файл
              :__table_dut      - тарувальна таблиця
        """
        self.__file_input = file_input
        self._chat_file = None
        self.__bot = bot
        self.__info = []
        self.__table_dut = None

    def _downloadfile(self):
        """
        Загрузчик файлу.
        :return:
        """
        # Отримання інформації про файл
        file_info = self.__bot.get_file(self.__file_input.document.file_id)

        # Завантажуэмо файл
        downloaded_file = self.__bot.download_file(file_info.file_path)
        self._chat_file = downloaded_file

        # Показать вміст файлу
        #self.__print_data_from_file(downloaded_file,True)

    def save_file_bitrek_excell(self):
        """
        Скачує надісланий з бота файл ексель в директорію, отримує тарувальну таблицю. В кінці отримання файл видаляється
        :return: None
        """
        file_info = self.__bot.get_file(self.__file_input.document.file_id)
        file_name = self.__file_input.document.file_name

        #Завантажили файл
        downloaded_file = self.__bot.download_file(file_info.file_path)

        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_file)

        df = pd.read_excel(file_name)

        table_data = []
        # Вывод всех строк и обработка их циклом
        for index, row in df.iterrows():
            #liters = row['Літри']
            #level = row['Рівень']
            #print(f"Строка {index}: Літри = {row['Літри']}, Рівень = {row['Рівень']}")
            table_data.append((int(row['Літри']), int(row['Рівень'])))
        self.__table_dut = table_data

        #Видаляємо тимчасову таблицю
        if os.path.exists(file_name):
            os.remove(file_name)

    def _get_encoding_file(self,downloaded_file):
        """
        Метод який повертає кодування файлу
        :param downloaded_file:   будь який файл
        :return:                  повертаэ кодування файлу toString
        """
        return chardet.detect(downloaded_file)['encoding']

    def _print_data_from_file(self,input_file, flag):
        """
        Вивід вмісту файлу. Підтримується декодування файлу. Якщо flag = True, то друк в консоль

        :param input_file       - вхідний файл
        :flag                   - якщо влаг True, то вивід вмісту файлу в консоль
        :return                 - toString
        """
        # Декодуємо байти в строку (якщо це текстовий файл)
        file_content = input_file.decode(self._get_encoding_file(input_file))
        if flag == True:
          print(file_content)
        return file_content

    def _extract_table_du02(self):
        """
        Функція відкриває отриманий файл і зберігає з нього інформацію
        self.__table_dut    - значення тарувальної таблиці [значення, літри]
        self.__info         - інформація про тарування

        :return: none
        """
        decode = self._get_encoding_file(self._chat_file)
        file_content = self._chat_file.decode(decode)

        table_data = []
        info = []
        capture_data = False

        for line in file_content.splitlines():

            if "Дата" in line or "Номер датчика" in line or "Предприятие" in line or \
                    "Автомобиль" in line or "Длина" in line or "Дискретность" in line:
                info.append(line.replace("\n", ''))
            # Перевіряємо чи почалась таблиця
            if "Объем" in line and "Число N" in line:
                capture_data = True
                continue

            # Закінчуємо обробку після кінця таблиці
            if "Тарировку выполнил" in line:
                info.append(line.replace("\n", ''))
                break

            # витягуємо дані із строк таблиці
            if capture_data:
                # шукаємо строки з числами
                matches = re.findall(r'\|\s*(\d+)\s*\|\s*(\d+)\s*\|', line)
                if matches:
                    for match in matches:
                        volume = int(match[0])  # Обєм
                        number_n = int(match[1])  # Число N
                        table_data.append((volume, number_n))
        #Записуємо таблицю в змінні класу
        # Сортування по другому елементу (Число N)
        sorted_data = sorted(table_data, key=lambda x: x[1])
        self.__table_dut = sorted_data
        self.__info = info

    def _get_table_dut(self):
        return self.__table_dut

    def _get_info(self):
        """
        :return: Повертає інформацію про тарувальну таблицю в однією строкою
        """
        #прибираємо зайві пробіли
        result = '\n'.join(map(lambda x: ' '.join(x.split()), self.__info))
        #прибираємо знаки підкреслювання
        result = result.replace("_", "").strip()
        result = result.replace("Гос. номер", "\nГос. номер")
        return result

    def _get_info_for_save(self):
        result = {}
        for line in self.__info:
            if "Дата" in line:
                result["Дата"] = line.split("Дата")[-1].strip()  # Извлекаем дату
            elif "Номер датчика (ID)" in line:
                result["Номер датчика (ID)"] = line.split("Номер датчика (ID)")[-1].strip()  # Извлекаем номер датчика
            elif "Номер пломбы" in line:
                result["Номер пломбы"] = line.split("Номер пломбы")[-1].strip()  # Извлекаем номер пломби
            elif "Предприятие" in line:
                result["Предприятие"] = line.split("Предприятие")[-1].strip()  # Извлекаем Предприятие

            elif "Автомобиль" in line:
                result["Автомобиль"] = line[line.find("Автомобиль") + 11:line.find(
                    "Гос. номер")].strip()  # Извлекаем Автомобиль
                result["Гос. номер"] = line.split("Гос. номер")[-1].strip()  # Извлекаем Автомобиль
            elif "Длина датчика уровня" in line:
                result["Длина датчика уровня"] = line.split("Длина датчика уровня")[-1].strip()
            elif "Дискретность тарировки" in line:
                result["Дискретность тарировки"] = line.split("Дискретность тарировки")[-1].strip()
            elif "Тарировку выполнил" in line:
                result["Тарировку выполнил"] = line.split("_______________")[-1].strip()

        return result

    def _save_to_file(self, data, output_file):
        """
        Збереження файлу з тарувальної таблиці в директорію 'fileeditor//' або вказану в output_file

        :param data: тарувальна таблиця
        :param output_file: Якщо Null, то формується назва файлу з інфрмації та зберігається таруальна таблиця
                            в файл в директорію fileeditor.
        :return: None
        """
        if output_file == None:
            temp = self._get_info_for_save()
            output_file = 'fileeditor//' + temp['Автомобиль'] +' ' + temp['Гос. номер'] + '.csv'

        with open(output_file, 'w', encoding='windows-1251') as file:
            file.write("Объем, Число N\n")
            for volume, number_n in data:
                file.write(f"{number_n}, {volume}\n")

    def _get_file_to_chat(self,data):
        """
        Функція що повертає дані з інформацією та файлом з тарувальною таблицею для бота
        :param data:
        :return:        Повертає ['інформація про таблицю'][потоковий файл]
        """
        # Створюємо файл в памяті
        output_file = io.StringIO()

        # Пхаємо дані в файл
        output_file.write("Объем, Число N\n")
        for volume, number_n in data:
            output_file.write(f"{number_n}, {volume}\n")

        #перемістити курсор в початок
        output_file.seek(0)

        temp = self._get_info()

        return [temp,output_file]


