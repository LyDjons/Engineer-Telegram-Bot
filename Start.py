from time import sleep

from openpyxl.descriptors import String
from openpyxl.xml.functions import tostring

from fileeditor.FileManager import FileManager
from config.config import TELEGRAM_TOKEN, WIALON_URL
from config.config import WIALON_TOKEN
from telebot import types
from WialonLocal.WialonManager import WialonManager
import telebot
import json
from WialonLocal.templates.Templates import LOGISTIC_MESSAGE_STATUS

bot = telebot.TeleBot(TELEGRAM_TOKEN)
# Словник для збереження станів виборів в меню Users
user_state = {}


# Головнне меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Сканування')
    btn2 = types.KeyboardButton('Тарувальна таблиця')
    btn3 = types.KeyboardButton('Інформація про бот 🤖')
    btn4 = types.KeyboardButton('Логістика')
    btn5 = types.KeyboardButton('Інженер GPS')
    clear_button = types.KeyboardButton("Ребут")
    markup.add(btn1, btn4)
    markup.add(btn2, btn5)
    markup.add(clear_button, btn3)
    return markup

# Підменю для пошуку
def logistic_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Вантажний транспорт')
    btn2 = types.KeyboardButton('<-Назад')
    markup.add(btn1, btn2)
    return markup


# Меню тарувальних таблиць
def fueltable_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Конвертер тарувальних таблиць')
    btn2 = types.KeyboardButton('<-Назад')
    markup.add(btn1, btn2)
    return markup


# Меню конвертер тарувальних таблиць
def fueltable_convert_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('ДУ-02 => Wialon.cvs')
    btn2 = types.KeyboardButton('Bitrek Sensor => Wialon.cvs')
    btn_test = types.KeyboardButton("TEST")
    btn3 = types.KeyboardButton('<-Назад')
    markup.add(btn1, btn2)
    markup.add(btn_test, btn3)
    return markup


def logistic_inline_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)  # row_width=2 сделает два столбика
    btn1 = types.InlineKeyboardButton('ЧІМК', callback_data='ЧІМК')
    btn2 = types.InlineKeyboardButton('СА', callback_data='СА')
    btn3 = types.InlineKeyboardButton('АП', callback_data='АП')
    btn4 = types.InlineKeyboardButton('БА', callback_data='БА')
    btn5 = types.InlineKeyboardButton('АК', callback_data='АК')
    btn6 = types.InlineKeyboardButton('ІМК', callback_data='ІМК')
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    return markup


def logistic_group_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Вантажний автотранспорт')
    btn2 = types.KeyboardButton('<-Назад')
    markup.add(btn1, btn2)
    return markup

def engineer_gps_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Меню пошуку')
    btn2 = types.KeyboardButton('Монтаж')
    btn3 = types.KeyboardButton('Демонтаж')
    btn4 = types.KeyboardButton('Заміна SIM')
    back = types.KeyboardButton('<-Назад')
    markup.add(btn1, btn2)
    markup.add(btn4, btn3)
    markup.add(back)
    return markup

def engineer_gps_search_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('По держ. номеру')
    btn2 = types.KeyboardButton('По EMEI')
    btn3 = types.KeyboardButton('По SIM')
    back = types.KeyboardButton('<-Назад')
    markup.add(btn1, btn2)
    markup.add(btn3, back)
    return markup

def ask_confirmation(message, count:int):
    # Створення інлайн-клавіатури
    markup = types.InlineKeyboardMarkup()
    button_yes = types.InlineKeyboardButton("ТАК", callback_data="yes")
    button_no = types.InlineKeyboardButton("НІ", callback_data="no")
    markup.add(button_yes, button_no)

    bot.send_message(message.chat.id, f"Знайдено в системі {count} об'єктів. Продовжити?", reply_markup=markup)


def test_function(message):
    bot.send_message(message.chat.id, f"Тестова функція. Тут нічо немає, тільки квадробобери")

@bot.message_handler(commands=['start'])
def start(message):
    chat_type = message.chat.type
    if chat_type == "private":
        bot.send_message(message.chat.id, "Доброго інженерного дня!", reply_markup=main_menu())


@bot.callback_query_handler(func=lambda call: call.data in ["yes", "no"])
def handle_callback(call):
    # Відповідно до вибору виконуються дії
    user_id = call.from_user.id
    if call.data == "yes" and user_state[user_id].get("wialon_json"):
        #bot.send_message(call.message.chat.id, f"```\n{user_state[user_id].get("wialon_json")}\n```", parse_mode="MarkdownV2")

        for i in user_state[user_id].get("wialon_json"):
            bot.send_message(call.message.chat.id, f"```\n{json.dumps(i, indent=4, ensure_ascii=False)}\n```", parse_mode="MarkdownV2")

        #обнуляємо навігацію користувача (історію його виборів в меню)
        user_state.pop(user_id, None)
        engineer_gps_search_menu()
    elif call.data == "no":
        # обнуляємо навігацію користувача (історію його виборів в меню)
        user_state.pop(user_id, None)
        bot.send_message(call.message.chat.id, "Як забажаєте.",reply_markup=engineer_gps_menu())
        return
    # Закриваємо "завантаження" кнопки
    bot.answer_callback_query(call.id)

# оброботчик, для меню, який першим оброблюэ повідомлення від користувача
@bot.message_handler(func=lambda message: message.text in ['Вантажний автотранспорт', 'Комбайни'])
def specific_handler(message):
    user_id = message.from_user.id
    user_state[user_id] = {'logistic_category': message.text}  # Зберігаємо вибрану категорію
    bot.send_message(message.chat.id, "Виберіть кластер:", reply_markup=logistic_inline_menu())
    #print(f"User ID: {user_id} вибрав : {message.text}\nUser State : {user_state}")


# оброботчик, для меню, який вибирає кластер
@bot.callback_query_handler(func=lambda call: call.data in ['ЧІМК', 'СА', 'АП', 'БА', 'АК', 'ІМК'])
def cluster_handler(call):
    user_id = call.from_user.id
    # Перевіряємо, чи вибрав User категорію
    if user_id not in user_state or 'logistic_category' not in user_state[user_id]:
        # Якщо в користувача нема збереженої категорії, перекидаєм на меню логістики
        bot.send_message(call.message.chat.id, "Порушена черга вибору. Почніть з головного меню.",
                         reply_markup=main_menu())
        return

    # Если состояние есть, выполняем действие в зависимости от выбора
    category = user_state[user_id]['logistic_category']
    cluster = call.data
    print(f"category = {category}")
    print(f"cluster = {cluster}")

    bot.send_message(call.message.chat.id, f"Ви вибрали:\n {category} => {cluster}\n\n"
                                           f"Нажаль, я не розумію чи працює техніка на підприємстві(\n"
                                           f"Я тільки показую наявність техніки в даній группі.\n\n"
                                           f"Я роблю аналіз, дочекайтесь його завершення...⏳")

    bot.answer_callback_query(call.id)
    # тут має щось запуститись

    # Удаляем состояние после выбора
    try:
        session = WialonManager(WIALON_URL, WIALON_TOKEN)
        print(call.message)
        print(session._get_info())
        print(generate_answer(category, cluster))
        json = session._create_my_json(generate_answer(category, cluster))

        # рахуємо к-ть обєктів в групі, що налажать різним кластерам
        count_objects = len(json["items"])
        item_count_chimc = 0
        item_count_ba = 0
        item_count_sa = 0
        item_count_ak = 0
        item_count_ap = 0
        item_nobody = 0
        count_other_clusters = 0
        count_rental = 0

        for item in json["items"].values():
            if "_" in item["nm"]:
                count_rental += 1
            if not item.get("property"):
                item_nobody = item_nobody + 1
            if item.get("property", {}).get("Власність") == "ТОВ ЧІМК":
                item_count_chimc = item_count_chimc + 1
                if cluster != "ЧІМК": count_other_clusters += 1
            if item.get("property", {}).get("Власність") == "ТОВ Бурат Агро":
                item_count_ba = item_count_ba + 1
                if cluster != "БА": count_other_clusters += 1
            if item.get("property", {}).get("Власність") == "ПП Агропрогрес":
                item_count_ap = item_count_ap + 1
                if cluster != "АП": count_other_clusters += 1
            if item.get("property", {}).get("Власність") == "ПСП Слобожанщина Агро":
                item_count_sa = item_count_sa + 1
                if cluster != "СА": count_other_clusters += 1
            if item.get("property", {}).get("Власність") == "ТОВ Агрокім":
                item_count_ak = item_count_ak + 1
                if cluster != "АК": count_other_clusters += 1

        # заповнюємо шаблон
        message_values = {
            "cluster_name": generate_answer(category, cluster),
            "cluster_count": count_objects,  # пофіксить вибір
            "count_cluster": item_count_chimc,
            "count_rental": count_rental,
            "other_clusters": count_other_clusters,  # пофіксить вибір
            "cluster_chimc": item_count_chimc if cluster != "ЧІМК" else 0,
            "cluster_ba": item_count_ba if cluster != "БА" else 0,
            "cluster_ak": item_count_ak if cluster != "АК" else 0,
            "cluster_sa": item_count_sa if cluster != "СА" else 0,
            "cluster_ap": item_count_ap if cluster != "АП" else 0,
        }

        formatted_message = LOGISTIC_MESSAGE_STATUS.format(**message_values)

        bot.send_message(call.message.chat.id, f"Я виконав запит {generate_answer(category, cluster)}")
        bot.send_message(call.message.chat.id, formatted_message)

    except Exception as e:
        print(f"Сталася помилка!: {e}")

    # обнуляєм навігацію користувача (історію його виборів в меню)
    user_state.pop(user_id, None)



@bot.message_handler(func=lambda message: True)
def menu_handler(message):
    if message.text == 'Меню пошуку':
        bot.send_message(message.chat.id, "Виберіть тип пошуку:", reply_markup=engineer_gps_search_menu())
    elif message.text == 'Логістика':
        bot.send_message(message.chat.id, "Зробіть ваш вибір:", reply_markup=logistic_group_menu())
    elif message.text == 'Інженер GPS':
        bot.send_message(message.chat.id, "Зробіть ваш вибір:", reply_markup=engineer_gps_menu())
    elif message.text == 'Тарувальна таблиця':
        bot.send_message(message.chat.id, "Зробіть ваш вибір:", reply_markup=fueltable_menu())
    elif message.text == 'Конвертер тарувальних таблиць':
        bot.send_message(message.chat.id, "Зробіть ваш вибір:", reply_markup=fueltable_convert_menu())
    elif message.text == 'Інформація про бот 🤖':
        bot.send_message(message.chat.id, "А я вам пакажу откудава готовілось нападєніє")
    elif message.text == 'По держ. номеру':
        bot.send_message(message.chat.id, "Введіть держ номер в форматі СВ1234ЕА:")
        #спочатку відбувається запуск reply_markup а потім текст_мессендж
        bot.register_next_step_handler(message, find_function)


    elif message.text in ['Монтаж', 'Демонтаж', 'Заміна SIM', 'По EMEI', 'По SIM']:
        bot.send_message(message.chat.id, "В процесі розробки")

    elif message.text == 'Ребут':
        bot.send_message(message.chat.id, "Колись зроблюю.")
    elif message.text == 'ДУ-02 => Wialon.cvs':
        bot.send_message(message.chat.id, "Відправте тарувальний файл з софту ДУ-02, я його переконвертую та "
                                          "поверну шаблон тарувальної таблиці для Wialon в форматі *.cvs")
        bot.register_next_step_handler(message, wait_for_file_DU02)
    elif message.text == 'Bitrek Sensor => Wialon.cvs':
        bot.send_message(message.chat.id, "Відправте тарувальний файл з софту Bitrek Sensor, я його переконвертую та "
                                          "поверну шаблон тарувальної таблиці для Wialon в форматі *.cvs")
        bot.register_next_step_handler(message, wait_for_file_BISensor)
    elif message.text == 'TEST':
        bot.send_message(message.chat.id,
                         'Ласкаво просимо до тестової функції, киньте якесь 💩, щоб приступити до тестування:')
        bot.register_next_step_handler(message, test_function)

    elif message.text == '<-Назад':
        bot.send_message(message.chat.id, "Повернення до головного меню", reply_markup=main_menu())

    else:
        bot.send_message(message.chat.id, "Щось пішло не так.Повернення до головного меню", reply_markup=main_menu())


def find_function(message):

    if message.text == "<-Назад":
        bot.send_message(message.chat.id, "Повернення до меню", reply_markup=engineer_gps_menu())
    if message.text in ["По EMEI", "По SIM", "По держ. номеру"]:
        bot.send_message(message.chat.id, "Ви не ввели держ. номер вручну!\nВиберіть знову критерій пошуку.")
        return
    plate_number = message.text.strip().upper()
    bot.send_message(message.chat.id, f"Ви ввели держ. номер = {plate_number}")

    # тут перевіряємо на правильність держномера
    if plate_number == "ALL" or (len(plate_number) == 8 and plate_number[:2].isalpha() and plate_number[2:6].isdigit() and plate_number[
                                                                                                 6:].isalpha()):
        bot.send_message(message.chat.id, f"Держ номер {plate_number} прийнято!")


        session = WialonManager(WIALON_URL, WIALON_TOKEN)
        print(session._get_info())


        my_json = session._get_list_universal("avl_unit",
                                              "sys_name",
                                              f"*{plate_number}*",
                                              "sys_name", 1, 1 + 256 + 1024 + 4096 + 2097152, 0, 10000)

        if len(my_json['items']) == 0:
            bot.send_message(message.chat.id, f"Вибачте, я не знайшов такого держ.номера")
            main_menu()
            return
        ask_confirmation(message,len(my_json['items']))

        user_state[message.from_user.id] = {'wialon_json': session._get_special_list_json(my_json)}  # Зберігаємо list_json в словник станів


    else:
        bot.send_message(message.chat.id, "Невірний формат." ,reply_markup=engineer_gps_search_menu())



def generate_answer(category: String, cluster: String):
    match (category, cluster):
        case ('Вантажний автотранспорт', 'АП'):
            return "АП Вантажні автомобілі 1 група"
        case ('Вантажний автотранспорт', 'АК'):
            return "АК Вантажні автомобілі 1 група"
        case ('Вантажний автотранспорт', 'СА'):
            return "СА Вантажні автомобілі 1 група"
        case ('Вантажний автотранспорт', 'БА'):
            return "БА Вантажні автомобілі 1 група"
        case ('Вантажний автотранспорт', 'ЧІМК'):
            return "ЧІМК Вантажні автомобілі 1 група"
        case ('Вантажний автотранспорт', 'ІМК'):
            return "ІМК Вантажні автомобілі 1 група"
        case _:
            return None


def wait_for_file_BISensor(message):
    """
       Функція обробки тарувальної таблиці для бітрек дутів від Bitrek
       1. Перевірка на файл.xls
       2. Завантаження файлу в директорію
       3. Відкриття файлу та отримання файл.csv для Wialon Local
       4.Видалення файлу файл.xls з директорії
       5.Відправка файл.csv в бот

       :param message: вхідне повідомлення з бота
       :return: None
       """
    try:
        if ((message.content_type == 'document')
                and (message.document.mime_type == 'application/x-msexcel')
                and ("xls" in message.document.file_name)):
            bot.send_message(message.chat.id, f"Файл {message.document.file_name}  Отримав. Починаю Конвертацію ⏳")

            converter = FileManager(message, bot)
            converter.save_file_bitrek_excell()
            if not converter._get_table_dut():
                bot.send_message(message.chat.id, "Файл пустий. Спробуй ще раз")
                return

            temp_file = converter._get_file_to_chat(converter._get_table_dut())
            file_name_to_save = message.document.file_name.rsplit('.', 1)[0] + ".csv"
            bot.send_document(message.chat.id, temp_file[1],
                              caption=f"Тут мала би бути інформація про тарування, але нажаль, її не має",
                              visible_file_name=file_name_to_save)

            bot.send_message(message.chat.id, "Конвертування таблиці завершилось успішно!", reply_markup=main_menu())
        elif message.text == '<-Назад':
            bot.send_message(message.chat.id, "Повернення до головного меню", reply_markup=main_menu())
        else:
            # Якщо відправлено не файл а щось інше
            bot.send_message(message.chat.id, "Щось пішло не так. Скинь тарувальну таблицю *.xls")
            bot.register_next_step_handler(message, wait_for_file_BISensor)  # Чекаєм знову файл
    except Exception as e:
        # Обрабатываем все исключения и отправляем сообщение об ошибке
        bot.send_message(message.chat.id, f"Виникла помилка: {str(e)}. Спробуй ще раз.")


# Обробка тарувальної таблиці ДУ-02
def wait_for_file_DU02(message):
    """
       \Функція обробки тарувальної таблиці для дутів ДУ-02
       1. Перевірка на файл.txt
       2. Завантаження файлу, отримання таблиці та парсинг інформації
       3. Отримання файл.csv для Wialon Local
       4.Відправка файл.csv в бот з Додатковою інформацією про тарування
       :param message: вхідне повідомлення з бота
       :return: None
       """

    # Перевірка на тип повідомлення (документ) та на розширення .txt
    if (message.content_type == 'document') and (message.document.mime_type == 'text/plain'):

        file_name = message.document.file_name
        bot.send_message(message.chat.id, f"Файл {file_name}  Отримав. Починаю Конвертацію ⏳")

        try:
            converter = FileManager(message, bot)
            converter._downloadfile()
            converter._extract_table_du02()
            if not converter._get_table_dut():
                bot.send_message(message.chat.id, "Файл пустий. Спробуй ще раз")
                return
            temp_file = converter._get_file_to_chat(converter._get_table_dut())

            json_data = json.dumps(converter._get_info_for_save(), indent=4, ensure_ascii=False)
            # json_data = "\n".join([f"*{key}:*\n{value}" for key, value in converter._get_info_for_save().items()])

            bot.send_document(message.chat.id, temp_file[1],
                              caption=f"Інформація про таблицю: ```json\n{json_data}\n``` ", parse_mode="MarkdownV2",
                              visible_file_name=(lambda info: f"{info['Автомобиль']} {info['Гос. номер']}")(
                                  converter._get_info_for_save()) + ".csv"
                              )
            bot.send_message(message.chat.id, "Конвертування таблиці завершилось успішно!", reply_markup=main_menu())
        except:
            bot.send_message(message.chat.id, "Критична помилка")

    elif message.text == '<-Назад':
        bot.send_message(message.chat.id, "Повернення до головного меню", reply_markup=main_menu())
    else:
        # Якщо відправлено не файл а щось інше
        bot.send_message(message.chat.id, "Щось пішло не так. Скинь тарувальну таблицю *.txt")
        bot.register_next_step_handler(message, wait_for_file_DU02)  # Чекаєм знову файл


bot.polling(none_stop=True)
