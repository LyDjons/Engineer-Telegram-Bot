from xml.etree.ElementTree import tostring
import re
info =[]

def file_manager(file_input):
    file_name = 'fileeditor//temp_file.txt'  # Путь к входному файлу
    #output_file = 'fileeditor//output_data.csv'  # Файл для записи результата

    #Зберігаємо тимчасовий файл
    save_file(file_input,file_name)

    # Извлекаем данные таблицы
    table_data = extract_table(file_name)

    # Сохраняем данные в новый файл


    temp = convert_info_du02(info)
    output_file = 'fileeditor//' + temp['Автомобиль'] +' ' + temp['Гос. номер'] + '.csv'

    save_to_file(table_data, output_file)

    return output_file

# save_file - записує отриманий результат у тимчасовий файл
def save_file(file_input,file_name):
    with open(file_name, 'wb') as new_file:
      new_file.write(file_input)

def extract_table(file_path):

    table_data = []
    capture_data = False

    with (open(file_path, 'r', encoding='windows-1251') as file):
        for line in file:

            if "Дата" in line or "Номер датчика" in line or "Предприятие" in line or \
               "Автомобиль" in line or "Длина" in line or "Дискретность" in line:
                info.append(line.replace("\n",''))
            # Проверяем, началась ли таблица
            if "Объем" in line and "Число N" in line:
                capture_data = True
                continue

            # Заканчиваем обработку после окончания таблицы
            if "Тарировку выполнил" in line:
                break

            # Извлекаем данные из строк таблицы
            if capture_data:
                # Ищем строки с числами
                matches = re.findall(r'\|\s*(\d+)\s*\|\s*(\d+)\s*\|', line)
                if matches:
                    for match in matches:
                        volume = int(match[0])  # Объем
                        number_n = int(match[1])  # Число N
                        table_data.append((volume, number_n))
    print(info)
    return table_data


def save_to_file(data, output_file):
    with open(output_file, 'w', encoding='windows-1251') as file:
        file.write("Объем, Число N\n")
        for volume, number_n in data:
            file.write(f"{number_n}, {volume}\n")

# convert_info_du02 - оброблюємо дані з інформацією файлу та повертаємо дані в словниковому типі
def convert_info_du02(information):
  result = {}

  for line in information:
      if "Дата" in line:
          result["Дата"] = line.split("Дата")[-1].strip()  # Извлекаем дату
      elif "Номер датчика (ID)" in line:
          result["Номер датчика (ID)"] = line.split("Номер датчика (ID)")[-1].strip()  # Извлекаем номер датчика
      elif "Номер пломбы" in line:
          result["Номер пломбы"] = line.split("Номер пломбы")[-1].strip()  # Извлекаем номер пломби
      elif "Предприятие" in line:
          result["Предприятие"] = line.split("Предприятие")[-1].strip()  # Извлекаем Предприятие

      #elif "Гос. номер" in line:
       #   result["Гос. номер"] = line.split("Гос. номер")[-1].strip()  # Извлекаем гос. номер
      elif "Автомобиль" in line:
          result["Автомобиль"] = line[line.find("Автомобиль")+11:line.find("Гос. номер")].strip()  # Извлекаем Автомобиль
          result["Гос. номер"] = line.split("Гос. номер")[-1].strip()  # Извлекаем Автомобиль
      elif "Длина датчика уровня" in line:
          result["Длина датчика уровня"] = line.split("Длина датчика уровня")[-1].strip()
      elif "Дискретность тарировки" in line:
          result["Дискретность тарировки"] = line.split("Дискретность тарировки")[-1].strip()


  return result






