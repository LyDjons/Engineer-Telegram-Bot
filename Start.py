from datetime import datetime
import re
from functools import wraps
from click.decorators import pass_meta_key
from telebot.asyncio_helper import delete_message

from fileeditor.FileManager import FileManager
from config.config import TELEGRAM_TOKEN, WIALON_URL, ENGINEER_CHAT_ID, THREAD_ID
from config.config import WIALON_TOKEN
from telebot import types
from WialonLocal.WialonManager import WialonManager
import telebot
import json
from WialonLocal.templates.Templates import LOGISTIC_MESSAGE_STATUS
from loader.ExcellLoader import ExcellLoader


bot = telebot.TeleBot(TELEGRAM_TOKEN)
message_mantle = "-"  # Спочатку ініціалізуємо змінну
mantling_state = {}
# Словник для збереження станів виборів в меню Users
user_state = {}
history_msg_mantling = {}


user_id_list = [5015926969,
                947585131,
                775847107,
                7746732602,
                7436821858,
                5019308388,
                811377535,
                405850921, #LyDjons
                353397138
                ]

# Состояния кнопок (начальные значения)
button_state = {"claster": ["-","ЧІМК","АП","АК","СА","БА"],
                "ownership": ["-","найманий","власний"],
                "власний": ["-","легкові","вантажні","трактора","комбайни","автобус","спецтехніка"],
                "найманий": ["-","вантажні","комбайни","авіація","трактора"],
                "легкові": ["-","патруль","безпека","інженерна","агрономічна","інші", "керівництво"],
                "вантажні": ["-","1 група","2 група"],
                "трактора": ["-","важкі","легкі"],
                }

# Декоратор для перевірки юзера
def check_permissions(func):
    @wraps(func)
    def wrapper(message_or_callback, *args, **kwargs):
        #print(f"arg = {isinstance(message_or_callback, telebot.types.Message)}")
        try:
            # Перевірка типу: якщо це callback_query
            if isinstance(message_or_callback, telebot.types.Message):  # це message
                message = message_or_callback
                print(f"User id: {message.from_user.id} username {message.from_user.username} push-> {message.text}")
            elif isinstance(message_or_callback, telebot.types.CallbackQuery):  # це callback_query
                callback_query = message_or_callback
                user = callback_query.from_user
                print(f"User id: {user.id} username {user.username} push-> {callback_query.data}")
            else:
                print("Unknown type of message_or_callback")

        except Exception as e:
            print(f"Error accessing mssage or callback_query: {e}")

        if message_or_callback.from_user.id not in user_id_list:
            bot.send_message(message_or_callback.chat.id,
                             "Хто ти, воїн?\nКинь 100 гривень на карту або йди геть\n\n"
                             "`444111115077246`", parse_mode="MarkdownV2")
            return
        return func(message_or_callback, *args, **kwargs)
    return wrapper


# Головнне меню
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Тест')
    btn2 = types.KeyboardButton('Тарувальна таблиця')
    btn3 = types.KeyboardButton('Інформація про бот 🤖')
    btn4 = types.KeyboardButton('Логістика')
    btn5 = types.KeyboardButton('Інженер GPS')
    clear_button = types.KeyboardButton("Ребут")
    markup.add(btn4, btn5)
    markup.add(btn2, btn3)
    #markup.add(clear_button, btn3)
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

def dismantling_gps_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Демонтаж по держ. номеру')
    btn2 = types.KeyboardButton('Демонтаж по EMEI')
    back = types.KeyboardButton('<-Назад')
    markup.add(btn1, btn2)
    markup.add( back)
    return markup

def mantle_stage_1_inline_keyboard(change_claster ='-', change_ownership='-', change_group='-', change_subgroup='-'):
    keyboard = types.InlineKeyboardMarkup()

    # Создание кнопок
    btn1 = types.InlineKeyboardButton("Клатер", callback_data="None")
    btn2 = types.InlineKeyboardButton("Власність", callback_data="None")
    btn3 = types.InlineKeyboardButton("Група", callback_data="None")
    btn4 = types.InlineKeyboardButton("Підгрупа", callback_data="None")
    confirm = types.InlineKeyboardButton("Підтвердити ✅", callback_data="confirm_mantling")
    cancel_mantle = types.InlineKeyboardButton("Відмінити ❌", callback_data="cancel_mantling")


    change_claster = types.InlineKeyboardButton(f"{change_claster}", callback_data="change_claster")
    change_ownership = types.InlineKeyboardButton(f"{change_ownership}", callback_data="change_ownership")
    change_group = types.InlineKeyboardButton(f"{change_group}", callback_data="change_group")
    change_subgroup = types.InlineKeyboardButton(f"{change_subgroup}", callback_data="change_subgroup")

    # Добавление кнопок в клавиатуру
    keyboard.add(btn1,change_claster)
    keyboard.add(btn2,change_ownership)
    keyboard.add(btn3,change_group)
    keyboard.add(btn4,change_subgroup)
    keyboard.add(confirm)
    keyboard.add(cancel_mantle)

    return keyboard

def mantle_stage_2_inline_keyboard(text_mark='-',text_model='-',text_number='-',text_driver='-'):
    keyboard = types.InlineKeyboardMarkup()

    # Создание кнопок
    btn1 = types.InlineKeyboardButton("Марка", callback_data="None")
    btn2 = types.InlineKeyboardButton("Модель", callback_data="None")
    btn3 = types.InlineKeyboardButton("Номер", callback_data="None")
    btn4 = types.InlineKeyboardButton("Водій", callback_data="None")
    confirm = types.InlineKeyboardButton("Підтвердити ✅", callback_data="confirm_mantling2")
    cancel_mantle = types.InlineKeyboardButton("Назад👈 ", callback_data="back_mantling")
    button_no = types.InlineKeyboardButton("Відхилити ❌", callback_data="cancel_mantling")

    change_mark = types.InlineKeyboardButton(f"{text_mark}", callback_data="change_mark")
    change_model = types.InlineKeyboardButton(f"{text_model}", callback_data="change_model")
    change_number = types.InlineKeyboardButton(f"{text_number}", callback_data="change_number")
    change_driver = types.InlineKeyboardButton(f"{text_driver}", callback_data="change_driver")
    clear_mark = types.InlineKeyboardButton(f"🔄", callback_data="update_mark")
    clear_model = types.InlineKeyboardButton(f"🔄", callback_data="update_model")
    clear_number = types.InlineKeyboardButton(f"🔄", callback_data="update_number")
    clear_driver = types.InlineKeyboardButton(f"🔄", callback_data="update_driver")

    # Добавление кнопок в клавиатуру
    keyboard.add(btn1,change_mark,clear_mark)
    keyboard.add(btn2,change_model,clear_model)
    keyboard.add(btn3,change_number,clear_number)
    keyboard.add(btn4,change_driver,clear_driver)
    keyboard.add(confirm)
    keyboard.add(cancel_mantle)
    keyboard.add(button_no)

    return keyboard

def mantle_stage_3_inline_keyboard():
    keyboard = types.InlineKeyboardMarkup()

    confirm = types.InlineKeyboardButton("Монтаж ✅", callback_data="confirm_mantling3")
    cancel_mantle = types.InlineKeyboardButton("Назад👈 ", callback_data="back_mantling2")
    button_no = types.InlineKeyboardButton("Відхилити ❌", callback_data="cancel_mantling")

    # Добавление кнопок в клавиатуру
    keyboard.add(confirm)
    keyboard.add(cancel_mantle)
    keyboard.add(button_no)

    return keyboard

def ask_approve_confirmation(specificator:str):
    # Створення інлайн-клавіатури
    markup = types.InlineKeyboardMarkup()
    button_yes = types.InlineKeyboardButton("Підтвердити ✅", callback_data="confirm_dismantle") #бот
    button_yes2 = types.InlineKeyboardButton("Погодити ✅", callback_data="approve_dismantle") #чат
    button_yes3 = types.InlineKeyboardButton("Підтвердити ✅", callback_data="approve_mantle")  # бот

    button_no = types.InlineKeyboardButton("Відхилити ❌", callback_data="decline_dismantle")

    if specificator == "confirm_dismantle":
        markup.add(button_yes, button_no)
    if specificator == "approve_dismantle":
        markup.add(button_yes2, button_no)
    if specificator == "approve_mantle":
        markup.add(button_yes3, button_no)
    return markup

def ask_confirmation(message, count:int, spec_message: str, specificator="simple"):
    # Створення інлайн-клавіатури
    markup = types.InlineKeyboardMarkup()

    button_yes = types.InlineKeyboardButton("ТАК", callback_data="yes")
    button_find_yes = types.InlineKeyboardButton("ТАК", callback_data="yes_find")
    button_dismantling_show = types.InlineKeyboardButton("ТАК", callback_data="show_dismantling")
    button_mantling_show = types.InlineKeyboardButton("ТАК", callback_data="show_mantling")

    button_no = types.InlineKeyboardButton("НІ", callback_data="no")

    if specificator =="simple":
        markup.add(button_yes, button_no)
    elif specificator=="find":
        markup.add(button_find_yes, button_no)
        spec_message = f"Зможу вивести тільки перші {count if count<10 else 10}" if count>1 else ""
    elif specificator == "dismantling":
        markup.add(button_dismantling_show, button_no)
    elif specificator == "mantling":
        markup.add(button_mantling_show, button_no)

    bot.send_message(message.chat.id, f"Знайдено в системі {count} об'єктів. {spec_message}\n Вивести результат?", reply_markup=markup)

def test_function(message):
    user_id = message.from_user.id  # Получаем ID пользователя
    username = message.from_user.username  # Получаем Username пользователя
    # Выводим ID и Username
    bot.reply_to(message, f"User ID: {user_id}\nUsername: @{username}")
    print(f"User ID: {user_id}\nUsername: @{username}")

def put_in_message_list(ures_id,message_id):
    """
    Функція яка записує всі повідомлення з чату в put_in_message_list щоб потім їх повидалять
    :param ures_id:
    :param message_id:
    :return:
    """
    if ures_id not in history_msg_mantling:
        history_msg_mantling[ures_id] = []
    history_msg_mantling[ures_id].append(message_id)  # Добавляем новый message_id в список

def delete_history_msg(message_chat_id):
    for msg in history_msg_mantling[message_chat_id]:
        bot.delete_message(chat_id=message_chat_id, message_id=msg)

    if message_chat_id in history_msg_mantling:
        del history_msg_mantling[message_chat_id]

def user_input_text_mantling2(message, additional_param: str):
    global message_mantle  # Якщо хочете використовувати глобальну змінну
    message_mantle = message.text  # Зберігаємо введене значення в змінну
    put_in_message_list(message.chat.id,message.id)

    msg = bot.send_message(message.chat.id, f"Ви ввели : {message_mantle}.\n"
                                      f"Натисніть для оновлення 🔄")
    put_in_message_list(message.chat.id, msg.message_id)


    if message.from_user.id not in mantling_state:
        mantling_state[message.from_user.id] = {
            "mark":"-",
            "model":"-",
            "number":"-",
            "driver":"-"
        }  # Если еще нет такого пользователя, создаем пустой словарь

    mantling_state[message.from_user.id][additional_param] = message.text  # Добавляем новый параметр

def check_mantling_status(claster_text, ownership_text, group_text, subgroup_text):
    """
    Функція перевіряє щоб всі групи були заповнені правильно
    :param claster_text: кластер
    :param ownership_text: власність
    :param group_text: група
    :param subgroup_text: підгрупа
    :return: True щк False
    """
    if claster_text == '-': return False
    if ownership_text == '-': return False
    if ownership_text == 'найманий' :return True
    if subgroup_text == '-' and group_text == '-': return False
    if subgroup_text == '-':
        if group_text in ["-","легкові","вантажні","трактора"]: return False
    return True

def add_to_wialon_group(obj_id,json_info,session):

    result = {
        'success': [],
        'not added': [],
         'already added': [],
         'not found group' : [],
         'none': []
    }

    temp_group = f"{json_info['Кластер']} Общая"

    #добавляєм в основні групи
    response = session._add_obj_to_group(obj_id,temp_group)
    result[response].append(temp_group)

    if json_info['Група'] == 'легкові':
        temp_group = f"{json_info['Кластер']} Легковий автотранспорт"
        response = session._add_obj_to_group(obj_id, temp_group)
        result[response].append(temp_group)
        if json_info['Підгрупа'] == 'патруль':
            temp_group = f"{json_info['Кластер']} ЛА Патрульна служба"
            response = session._add_obj_to_group(obj_id, temp_group)
            result[response].append(temp_group)
            #Добавляємо в ІМК патрульна служба
            temp_group = "ІМК патрульна служба"
            response = session._add_obj_to_group_for_groupID(obj_id, 2275)
            result[response].append(temp_group)
        if json_info['Підгрупа'] == 'безпека':
            temp_group = f"{json_info['Кластер']} ЛА Служба безпеки"
            response = session._add_obj_to_group(obj_id, temp_group)
            result[response].append(temp_group)
        if json_info['Підгрупа'] == 'інженерна':
            temp_group = f"{json_info['Кластер']} ЛА Інженерна служба"
            response = session._add_obj_to_group(obj_id, temp_group)
            result[response].append(temp_group)
        if json_info['Підгрупа'] == 'агрономічна':
            temp_group = f"{json_info['Кластер']} ЛА Агрономічна служба"
            response = session._add_obj_to_group(obj_id, temp_group)
            result[response].append(temp_group)
        if json_info['Підгрупа'] == 'інші':
            temp_group = f"{json_info['Кластер']} ЛА Інші служби"
            response = session._add_obj_to_group(obj_id, temp_group)
            result[response].append(temp_group)
        if json_info['Підгрупа'] == 'керівництво':
            temp_group = f"{json_info['Кластер']} ЛА Керівництво"
            response = session._add_obj_to_group(obj_id, temp_group)
            result[response].append(temp_group)

    if json_info['Група'] == 'вантажні':
        if json_info['Підгрупа'] =='1 група':
            temp_group = f"{json_info['Кластер']} Вантажні автомобілі 1 група"
            response = session._add_obj_to_group(obj_id, temp_group)
            result[response].append(temp_group)
        if json_info['Підгрупа'] =='2 група':
            temp_group = f"{json_info['Кластер']} Вантажні автомобілі 2 група"
            response = session._add_obj_to_group(obj_id, temp_group)
            result[response].append(temp_group)
        if json_info['Власність'] =='найманий':
            temp_group = f"{json_info['Кластер']} Вантажні автомобілі 1 група"
            response = session._add_obj_to_group(obj_id, temp_group)
            result[response].append(temp_group)

    if json_info['Група'] == 'комбайни':

        temp_group = f"{json_info['Кластер']} Комбайни"
        response = session._add_obj_to_group(obj_id, temp_group)
        result[response].append(temp_group)

    if json_info['Група'] == 'автобус':
        temp_group = f"{json_info['Кластер']} Автобуси"
        response = session._add_obj_to_group(obj_id, temp_group)
        result[response].append(temp_group)

    if json_info['Група'] == 'спецтехніка':
        temp_group = f"{json_info['Кластер']} Спецтехніка"
        response = session._add_obj_to_group(obj_id, temp_group)
        result[response].append(temp_group)

    if json_info['Група'] == 'авіація':
        temp_group = "ІМК Авіація"
        response = session._add_obj_to_group_for_groupID(obj_id,1404)
        result[response].append(temp_group)

    if json_info['Власність'] == 'найманий':
        if json_info['Група'] != 'авіація':
            temp_group = f"{json_info['Кластер']} історія"
            response = session._add_obj_to_group(obj_id, temp_group)
            result[response].append(temp_group)

    return result

@bot.callback_query_handler(func=lambda call: call.data in ["change_claster","change_ownership","confirm_mantling",
                                                            "change_group","change_subgroup","cancel_mantling",
                                                            "back_mantling","change_mark","change_model",
                                                            "change_number","change_driver","update_mark","update_model",
                                                            "update_number","update_driver","confirm_mantling2",
                                                            "confirm_mantling3","back_mantling2","approve_mantle"])
@check_permissions
def callback_mantling(call):

    # Текст натиснутих кнопок
    keyboard_data = call.message.json.get('reply_markup').get('inline_keyboard')
    claster_text = get_button_text_by_callback('change_claster', keyboard_data)
    ownership_text = get_button_text_by_callback('change_ownership', keyboard_data)
    group_text = get_button_text_by_callback('change_group', keyboard_data)
    subgroup_text = get_button_text_by_callback('change_subgroup', keyboard_data)
    mark_text = get_button_text_by_callback('change_mark', keyboard_data)
    model_text = get_button_text_by_callback('change_model', keyboard_data)
    number_text = get_button_text_by_callback('change_number', keyboard_data)
    driver_text = get_button_text_by_callback('change_driver', keyboard_data)
    global message_mantle
    #print(f"callback= {call.data}")
    """print(f"Дані кнопок :\n "
                            f"{claster_text}\n"
                            f"{ownership_text}\n"
                            f"{group_text}\n"
                            f"{subgroup_text}"
                            )"""
    """print(f"Дані кнопок :\n "
                                f"mark={mark_text}\n"
                                f"model={model_text}\n"
                                f"number={number_text}\n"
                                f"driver={driver_text}"
                                )"""
    #якщо натиснута кнопка вибору кластеру
    if call.data == "change_claster":

        #по отриманому значенні кнопки отримуємо індекс наступної в словнику по ключу claster
        next_index = button_state["claster"].index(claster_text) + 1
        if next_index > len(button_state["claster"]) - 1:
            next_index = 1
        keyboard = mantle_stage_1_inline_keyboard(change_claster=button_state["claster"][next_index],
                                                  change_ownership=ownership_text,
                                                  change_group=group_text,
                                                  change_subgroup=subgroup_text)

        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )

    if call.data == "change_ownership":
        # дані всіх кнопок
        next_index = button_state["ownership"].index(ownership_text) + 1
        if next_index > len(button_state["ownership"]) - 1:
            next_index = 1
        keyboard = mantle_stage_1_inline_keyboard(change_claster=claster_text,
                                                  change_ownership=button_state["ownership"][next_index],
                                                  change_group="-",
                                                  change_subgroup="-")

        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )

    if call.data == "change_group":

        # залежно від власності вибираємо необхідний список груп
        key_list = "-"
        if ownership_text == "власний":
            key_list = "власний"
        if ownership_text == "найманий":
            key_list = "найманий"


        next_index = button_state[key_list].index(group_text) + 1
        if next_index > len(button_state[key_list]) - 1:
            next_index = 1
        keyboard = mantle_stage_1_inline_keyboard(change_claster=claster_text,
                                                  change_ownership=ownership_text,
                                                  change_group=button_state[key_list][next_index],
                                                  change_subgroup="-")

        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )

    # залежно від групи вибираємо необхідний список підгруп
    if call.data == "change_subgroup":
        key_list = "-"
        if group_text == "легкові":
            key_list = "легкові"
        if group_text == "вантажні":
            key_list = "вантажні"
        if group_text == "трактора":
            key_list = "трактора"

        else:
            if key_list == '-': return
        next_index = button_state[key_list].index(subgroup_text) + 1
        if next_index > len(button_state[key_list]) - 1:
            next_index = 1

        subgroup_text = button_state[key_list][next_index]

        # для найманої техніки відсутні підгрупи
        if ownership_text == "найманий":
            subgroup_text = "-"

        #тут якщо підгрупа не може змінюватись (бо наймана техніка) може виникати помилка
        #бо стан не змінюється, тому берем в try
        try:

            keyboard = mantle_stage_1_inline_keyboard(change_claster=claster_text,
                                                      change_ownership=ownership_text,
                                                      change_group=group_text,
                                                      change_subgroup=subgroup_text)

            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=keyboard
            )
        except Exception as e:
            #print(f"Нема чого оновлювати: {e}")
            pass

    if call.data == "confirm_mantling":

        if check_mantling_status(claster_text,ownership_text,group_text,subgroup_text) == False:
            msg = bot.send_message(call.message.chat.id,"Виберіть правильно кластер, власність, групи та підгрупи")
            put_in_message_list(call.message.chat.id, msg.message_id)
            return
        #в повідомленні 2 json. Витягуємо їх із call.message.text та перетворюємо в json для подальшого обробітку
        json_match = re.findall(r'\{(.*?)\}',call.message.text,re.DOTALL)
        json1 = "{" + json_match[0].strip().replace("\n", "").replace("    ", "") + "}"
        json1 = json.loads(json1)
        json2 = "{" + json_match[1].strip().replace("\n", "").replace("    ", "") + "}"
        json2 = json.loads(json2)

        #print(json1)
        #print(json2)
        #print(f"all button: {call.message.json.get('reply_markup').get('inline_keyboard')}")
        text_cluster = call.message.json.get('reply_markup').get('inline_keyboard')[0][1].get('text')

        json2['Кластер'] = text_cluster
        json2['Операція'] = 'Монтаж'
        json2['Власність'] = ownership_text
        json2['Група'] = group_text
        json2['Підгрупа'] = subgroup_text


        json2['Марка'] = "-" if json2['Марка'] in ["-","",None] else json2['Марка']
        json2['Модель'] = "-" if json2['Модель'] in ["-","",None] else json2['Модель']
        json2['Номер'] = "-" if json2['Номер'] in ["-","",None] else json2['Номер']
        json2['Водитель'] = "-" if json2['Водитель'] in ["-","",None] else json2['Водитель']

        # Используем обратные кавычки для отображения в формате кода
        # formatted_text = "```\n" + json.dumps(text, indent=4, ensure_ascii=False) + "\n```"
        formatted_text = f"```\n{json.dumps(json1, indent=4, ensure_ascii=False)}\n```\n```\n{json.dumps(json2, indent=4,ensure_ascii=False)}\n```"

        #keyboard = mantle_stage_1_inline_keyboard(change_claster=text_cluster)
        keyboard2 = mantle_stage_2_inline_keyboard(text_mark=json2['Марка'],
                                                   text_model=json2['Модель'],
                                                   text_number=json2['Номер'],
                                                   text_driver=json2['Водитель'])

        # Обновляем сообщение с новой клавиатурой
        bot.edit_message_text(
            formatted_text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard2,
            parse_mode='Markdown'
        )

    if call.data == "back_mantling2":

        json_match = re.findall(r'\{(.*?)\}', call.message.text, re.DOTALL)
        json1 = "{" + json_match[0].strip().replace("\n", "").replace("    ", "") + "}"
        json1 = json.loads(json1)
        json2 = "{" + json_match[1].strip().replace("\n", "").replace("    ", "") + "}"
        json2 = json.loads(json2)

        formatted_text = f"```\n{json.dumps(json1, indent=4, ensure_ascii=False)}\n```\n```\n{json.dumps(json2, indent=4, ensure_ascii=False)}\n```"
        keyboard2 = mantle_stage_2_inline_keyboard(text_mark=json2['Марка'],
                                                   text_model=json2['Модель'],
                                                   text_number=json2['Номер'],
                                                   text_driver=json2['Водитель'])


        # Обновляем сообщение с новой клавиатурой
        bot.edit_message_text(
            formatted_text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard2,
            parse_mode='Markdown'
        )

    if call.data == "back_mantling":

        json_match = re.findall(r'\{(.*?)\}', call.message.text, re.DOTALL)
        #json1 = "{" + json_match[0].strip().replace("\n", "").replace("    ", "") + "}"
        #json1 = json.loads(json1)
        json2 = "{" + json_match[1].strip().replace("\n", "").replace("    ", "") + "}"
        json2 = json.loads(json2)

        #text_cluster = call.message.json.get('reply_markup').get('inline_keyboard')[0][1].get('text')

        # Используем обратные кавычки для отображения в формате кода
        #formatted_text = f"```\n{json.dumps(json1, indent=4, ensure_ascii=False)}\n```\n```\n{json.dumps(json2, indent=4, ensure_ascii=False)}\n```"


        keyboard = mantle_stage_1_inline_keyboard(change_claster=json2['Кластер'],
                                                  change_ownership=json2['Власність'],
                                                  change_group=json2['Група'],
                                                  change_subgroup=json2['Підгрупа'])

        bot.edit_message_reply_markup(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )

    if call.data == "change_mark":
        msg = bot.send_message(call.message.chat.id, "Введіть марку транспорту:")
        put_in_message_list(call.message.chat.id,msg.message_id)

        bot.register_next_step_handler(call.message,
                                       lambda message: user_input_text_mantling2(message, "mark"))

    if call.data == "change_model":
        msg = bot.send_message(call.message.chat.id, "Введіть модель транспорту:")
        put_in_message_list(call.message.chat.id, msg.message_id)

        bot.register_next_step_handler(call.message,
                                       lambda message: user_input_text_mantling2(message, "model"))

    if call.data == "change_number":
        msg = bot.send_message(call.message.chat.id, "Введіть держ. транспорту:")
        put_in_message_list(call.message.chat.id,msg.message_id)

        bot.register_next_step_handler(call.message,
                                       lambda message: user_input_text_mantling2(message, "number"))

    if call.data == "change_driver":
        msg = bot.send_message(call.message.chat.id, "Введіть водія транспорту:")
        put_in_message_list(call.message.chat.id, msg.message_id)

        bot.register_next_step_handler(call.message,
                                       lambda message: user_input_text_mantling2(message, "driver"))

    if call.data == "update_mark":
        if call.message.chat.id in history_msg_mantling : delete_history_msg(call.message.chat.id)

        if call.from_user.id not in mantling_state:
            return  # якщо такого користувача немає

        try:
            keyboard = mantle_stage_2_inline_keyboard(text_mark=mantling_state[call.from_user.id]["mark"],
                                                      text_model=model_text,
                                                      text_number=number_text,
                                                      text_driver=driver_text)
            mantling_state[call.from_user.id]["mark"] = "-"

            bot.edit_message_reply_markup(chat_id=call.message.chat.id,message_id=call.message.message_id,
                                          reply_markup=keyboard)
        except Exception as e:
            # print(f"Нема чого оновлювати: {e}")
            pass
        message_mantle = "-"

    if call.data == "update_model":
        if call.message.chat.id in history_msg_mantling: delete_history_msg(call.message.chat.id)
        if call.from_user.id not in mantling_state:
            return  # якщо такого користувача немає
        try:
            keyboard = mantle_stage_2_inline_keyboard( text_mark=mark_text,
                                                       text_model=mantling_state[call.from_user.id]["model"],
                                                    text_number=number_text,
                                                       text_driver=driver_text)
            mantling_state[call.from_user.id]["model"] = "-"
            bot.edit_message_reply_markup(chat_id=call.message.chat.id,message_id=call.message.message_id,
                                        reply_markup=keyboard)
        except Exception as e:
            #print(f"Нема чого оновлювати: {e}")
            pass
        message_mantle = "-"

    if call.data == "update_number":
        if call.message.chat.id in history_msg_mantling: delete_history_msg(call.message.chat.id)
        if call.from_user.id not in mantling_state:
            return  # якщо такого користувача немає
        try:
            keyboard = mantle_stage_2_inline_keyboard(text_mark=mark_text,
                                                      text_model=model_text,
                                                      text_number=mantling_state[call.from_user.id]["number"].upper(),
                                                      text_driver=driver_text)
            mantling_state[call.from_user.id]["number"] = "-"
            bot.edit_message_reply_markup(
                    chat_id=call.message.chat.id,message_id=call.message.message_id,reply_markup=keyboard
            )
        except Exception as e:
            # print(f"Нема чого оновлювати: {e}")
            pass
        message_mantle = "-"

    if call.data == "update_driver":
        if call.message.chat.id in history_msg_mantling: delete_history_msg(call.message.chat.id)
        if call.from_user.id not in mantling_state:
            return  # якщо такого користувача немає
        try:
            keyboard = mantle_stage_2_inline_keyboard(text_mark=mark_text,
                                                      text_model=model_text,
                                                      text_number=number_text,
                                                      text_driver=mantling_state[call.from_user.id]["driver"])
            mantling_state[call.from_user.id]["driver"] = "-"

            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,message_id=call.message.message_id,reply_markup=keyboard)
        except Exception as e:
            # print(f"Нема чого оновлювати: {e}")
            pass
        message_mantle = "-"

    if call.data == "cancel_mantling":
        # видаляємо повідомлення
        bot.delete_message(call.message.chat.id, call.message.message_id)
        message_mantle = "-"
        if call.from_user.id in mantling_state:
            del mantling_state[call.from_user.id]

    if call.data == "confirm_mantling2":

        if mark_text == "-" or number_text == "-":
            msg = bot.send_message(call.message.chat.id, "Поля Марка та держ.номер обов'язкові до заповнення")
            put_in_message_list(call.message.chat.id, msg.message_id)
            return

        #перевірка держномера на англ.символи
        if not all(('а' <= c <= 'я' or 'А' <= c <= 'Я' or c in 'ієїІЇ' or c.isdigit()) for c in number_text):
            msg = bot.send_message(call.message.chat.id, f"Держ.номер {number_text} введений ENG 🇺🇸 літерами!")
            put_in_message_list(call.message.chat.id, msg.message_id)

        try:
            session = WialonManager(WIALON_URL,WIALON_TOKEN)
            result = session._get_list_universal("avl_unit",
                                              "sys_name",
                                              f"*{number_text}*",
                                              "sys_name", 1, 1 +256, 0, 10000)
            if result["items"]:
                #print(result["items"])
                msg = bot.send_message(call.message.chat.id, f"Об'єкт з держ. {number_text} знайдено у Wialon ✅ ")
                put_in_message_list(call.message.chat.id, msg.message_id)

            if not result["items"]:
                msg = bot.send_message(call.message.chat.id, f"Об'єкт з держ. {number_text} не знайдено у Wialon ❌\n"
                                                             f"Буде створений новий ✅")
                put_in_message_list(call.message.chat.id, msg.message_id)


        except:
            print("error")
            pass

        # в повідомленні 2 json. Витягуємо їх із call.message.text та перетворюємо в json для подальшого обробітку
        json_match = re.findall(r'\{(.*?)\}', call.message.text, re.DOTALL)
        json1 = "{" + json_match[0].strip().replace("\n", "").replace("    ", "") + "}"
        json1 = json.loads(json1)
        json2 = "{" + json_match[1].strip().replace("\n", "").replace("    ", "") + "}"
        json2 = json.loads(json2)

        json2['Марка'] = mark_text
        json2['Модель'] = model_text if model_text != "-" else "-"
        json2['Номер'] = number_text
        json2['Водитель'] = driver_text if driver_text!= "-" else "-"
        json2['ініціатор'] = call.from_user.username

        formatted_text = f"```\n{json.dumps(json1, indent=4, ensure_ascii=False)}\n```\n```\n{json.dumps(json2, indent=4, ensure_ascii=False)}\n```"

        # keyboard = mantle_stage_1_inline_keyboard(change_claster=text_cluster)
        """keyboard2 = mantle_stage_2_inline_keyboard(text_mark=json2['Марка'],
                                                   text_model=json2['Модель'],
                                                   text_number=json2['Номер'],
                                                   text_driver=json2['Водитель'])"""
        keyboard3 = mantle_stage_3_inline_keyboard()

        # Обновляем сообщение с новой клавиатурой
        bot.edit_message_text(
            formatted_text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard3,
            parse_mode='Markdown'
        )

    if call.data == "confirm_mantling3":

        message_text = call.message.text
        try:
            bot.send_message(ENGINEER_CHAT_ID, f"```\n{message_text}\n```",
                             parse_mode="MarkdownV2",
                             reply_markup=ask_approve_confirmation("approve_mantle"),
                             message_thread_id=THREAD_ID)
        except Exception as e:
            bot.send_message(call.message.chat.id, f"Не знайдено чат з ID={ENGINEER_CHAT_ID} та THREAD_ID={THREAD_ID}")
            return

        # Удаляем сообщение в чате бота после отправки
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, f"```\n{message_text}\n```Монтаж відправлено в основний чат",
                         parse_mode="MarkdownV2")

    if call.data == "approve_mantle":
        print(f"User : {call.from_user.id} name = {call.from_user.first_name} "
              f"push '{call.data}' "
              f"Chat ID '{call.message.chat.id}' "
              f"message_thread_id = {getattr(call.message, 'message_thread_id', 'No thread ID')}")

        # Коли в чат падає заявка, то тільки адміністратор або власник може натиснути "Погодити"
        try:
            chat_member = bot.get_chat_member(call.message.chat.id, call.from_user.id)
            print(f"Role: {chat_member.status}")
            if chat_member.status not in ["administrator", "creator"]:
                return
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Ошибка: {e}")
            bot.send_message(call.message.chat.id, f"Помилка ролі", message_thread_id=THREAD_ID)
            return

        # Зберігаємо  ідентифікатор старого повідомлення
        old_message_id = call.message.message_id

        # Якшо пілся наших jsons є якийсь текст, то ми його відкидаємо
        index_symb = call.message.text.rfind('}')
        if index_symb != -1:
            message_text = call.message.text[:index_symb + 1]  # Включаем саму скобку

        #Парсимо json 1 та json 2
        json_match = re.findall(r'\{(.*?)\}', message_text, re.DOTALL)
        json1 = "{" + json_match[0].strip().replace("\n", "").replace("    ", "") + "}"
        json1 = json.loads(json1)
        json2 = "{" + json_match[1].strip().replace("\n", "").replace("    ", "") + "}"
        json2 = json.loads(json2)

        # Извлекаем текст после JSON объектов
        after_json_text = message_text.split('}'.join(json_match[:2]))[-1].strip()

        message_time = call.message.date

        # Преобразуем Unix timestamp в читаемый формат
        readable_time = datetime.fromtimestamp(message_time)
        # print(f"Value of 'nm': {nm_value}")

        # Отримуємо поточну дату та час
        current_datetime = datetime.now()
        # Форматуємо дату та час
        formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
        # Вычисление разницы во времени
        delay = current_datetime - readable_time

        # формуємо нову назву для об'єкту
        obj_new_name = ""
        if json2['Власність'] == 'найманий': obj_new_name += f"{json2['Кластер']}_"
        obj_new_name += json2['Марка']
        if json2['Модель'] != '-': obj_new_name += f" {json2['Модель']}"
        obj_new_name += f" ({json2['Номер']})"
        if json2['Водитель'] != '-': obj_new_name += f" {json2['Водитель']}"

        success__description_logs = {
            'success': [],
            'errors': []

        }
        error_description = ""  # лог помилок при створенні об'єкта
        protocol_name = ""
        sim=""
        obj_new_name = obj_new_name[:50] if len(obj_new_name) > 50 else obj_new_name

        temp_obj = 0

        try:
            info_wialon = WialonManager(WIALON_URL, WIALON_TOKEN)
            # #перевіряємо держномер у Wialon
            temp_obj = info_wialon._get_list_universal("avl_unit",
                                              "sys_name",
                                              f"*({json2['Номер']})*",
                                              "sys_name", 1, 1 + 256 , 0, 10000)


            if len(temp_obj['items']) > 1:
                bot.send_message(call.message.chat.id, f"Вибачте, я знайшов декілька об'єктів з таким держ. номером\n"
                                                       f"Видаліть зайвий і спробуйте знову", message_thread_id=THREAD_ID)
                return

            #Якщо знайдено один об'єкт або не знайдено жодного
            if len(temp_obj['items']) == 0 or len(temp_obj['items']) == 1:

                # Якщо не знайдено то створюємо
                if len(temp_obj['items']) == 0:
                    # Визначення протоколу та id_creator

                    print(json2["Кластер"]=="CА")
                    creator_id = info_wialon._get_creator_if_from_claster_ua(json2["Кластер"])
                    protocol_id = info_wialon._get_id_and_pass_protocol_for_user_mask(json1["Серия"])[0]
                    protocol_name = info_wialon._device_type(protocol_id)


                    create_result = info_wialon._create_obj(creator_id, obj_new_name, protocol_id)
                    print(f"creator id={creator_id} protocol id = {protocol_id} protocol name = {protocol_name}")


                    success__description_logs['success'].append(f"Створено об'єкт = {obj_new_name}"
                                                                f" Creator_id = {creator_id}"
                                                                f" protocol_id = {protocol_id}")

                    temp_obj = info_wialon._get_list_universal("avl_unit",
                                                               "sys_name",
                                                               f"*({json2['Номер']})*",
                                                               "sys_name", 1, 1 + 256, 0, 10000)

                    if "error" in create_result:
                        if create_result['error']==6:
                            error_description += error_description + f"Відсутні вільні обєкти в Wialon Local❌"
                        if create_result['error']==4:
                            error_description += error_description + f"Не зміг створить обєкт в Wialon Local❌"
                        success__description_logs['errors'].append(error_description)

                        formatted_text = (f"```\n{json.dumps(json1, indent=4, ensure_ascii=False)}\n```\n"
                                          f"```\n{json.dumps(json2, indent=4, ensure_ascii=False)}\n```"
                                          f"{error_description}")
                        # Оновлюємо повідомлення в чаті і добавляємо текст помилки
                        try:
                            bot.edit_message_text(
                                formatted_text,
                                chat_id=ENGINEER_CHAT_ID,
                                message_id=call.message.message_id,
                                reply_markup=ask_approve_confirmation("approve_mantle"),
                                parse_mode='Markdown'
                            )
                            return
                        except Exception as e:
                            #тут бажано ще перевірить на можливість відправки в інженерний чат та потрібну гілку
                            print("Не вдалось оновити Message Telegram. Відсутні вільні обєкти в Wialon Local")
                            return
                            pass

                if len(temp_obj['items']) == 1:
                    success__description_logs["success"].append(
                        f"Знайдено в Wialon по держ. = {temp_obj['items'][0]['nm']}")

                # то добавиться повідомлення
                if temp_obj['items'][0]['uid'] != "":
                    # Оновлюємо повідомлення й додаємо error
                    error_description = (f"❌Я не можу провести монтаж\n "
                                         f"Об'єкт= {temp_obj['items'][0]['nm']} \nУже має IMEI= {temp_obj['items'][0]['uid']}")
                    success__description_logs["errors"].append(error_description)

                    # Экранируем специальные символы Markdown
                    # error_description = re.sub(r'([`\*_{}[\]()#+\-.!])', r'\\\1', error_description)
                    error_description = re.sub(r'([`\*_{}[\]#+\-.!])', r'\\\1', error_description)

                    formatted_text = (f"```\n{json.dumps(json1, indent=4, ensure_ascii=False)}\n```\n"
                                      f"```\n{json.dumps(json2, indent=4, ensure_ascii=False)}\n```"
                                      f"{error_description}")
                    # Оновлюємо повідомлення в чаті і добавляємо текст помилки
                    try:
                        bot.edit_message_text(
                            formatted_text,
                            chat_id=ENGINEER_CHAT_ID,
                            message_id=call.message.message_id,
                            reply_markup=ask_approve_confirmation("approve_mantle"),
                            parse_mode='Markdown'
                        )
                    except Exception as e:
                        pass
                    print(error_description)
                    return

                # якщо обєкт без EMEI
                if temp_obj['items'][0]['uid'] == "":
                    # Отримуємо id протокола і загальноприйнятий пароль [23,"1111"]
                    id_protocol_pass = info_wialon._get_id_and_pass_protocol_for_user_mask(json1["Серия"])
                    # update IMEI and protocol
                    info_wialon._update_protocol_imei(temp_obj['items'][0]['id'], id_protocol_pass[0],
                                                      json1['ИМЕИ'])
                    success__description_logs["success"].append(f"Update imei = {json1['ИМЕИ']}")
                    success__description_logs["success"].append(f"Update_protocol = {id_protocol_pass[0]}")

                    # добавить сімку
                    response = info_wialon._update_phone(temp_obj['items'][0]['id'], f"%2B38{json1['Телефон']}")
                    sim = json1['Телефон']

                    # 'error' свідчить про те що SIM уже десь використовується у Віалоні
                    if 'error' in response:
                        name_with_phone = info_wialon._get_name_obj_for_device_phone(phone=f"*{json1['Телефон']}")
                        info_wialon._update_phone(temp_obj['items'][0]['id'], "")
                        sim =""
                        error_description += f"Не вдалось прописати SIM карту. Уже є в об'єкті: {name_with_phone}"
                        success__description_logs["errors"].append(error_description)
                    else:
                        success__description_logs["success"].append(f"Update sim = {json1['Телефон']}")

                # добавляємо пароль протоколу
                info_wialon._update_protocol_password(temp_obj['items'][0]['uid'], id_protocol_pass[1])
                success__description_logs["success"].append(f"Update pass protocol = {id_protocol_pass[1]}")

                # добавляємо обєкт в групи
                result_group_added = add_to_wialon_group(temp_obj['items'][0]['id'], json2, info_wialon)
                success__description_logs["success"].append(f"Add to groups: {result_group_added}")

                # перейменовуємо obj
                info_wialon._rename_unit(temp_obj['items'][0]['id'], obj_new_name)
                success__description_logs["success"].append("Перейменовано об'єкт")

                # добавляємо та перейменовуємо датчик
                result_sensors = info_wialon._create_udate_voltage_sensors(temp_obj['items'][0]['id'])
                success__description_logs["success"].append(f"Update sensors: {result_sensors}")

                # якщо найм то оновлюємо icon
                if json2['Власність'] == "найманий" and json2['Група'] == "вантажні":
                    info_wialon._change_icon_hired(temp_obj['items'][0]['id'])
                    success__description_logs["success"].append("change icon")

                formatted_text = (f"```\n{json.dumps(json1, indent=4, ensure_ascii=False)}\n```\n"
                                  f"```\n{json.dumps(json2, indent=4, ensure_ascii=False)}\n```"
                                  f"{error_description}")

                bot.edit_message_text(
                    formatted_text,
                    chat_id=ENGINEER_CHAT_ID,
                    message_id=call.message.message_id,
                    reply_markup=ask_approve_confirmation("approve_mantle"),
                    parse_mode='Markdown'
                )


        except Exception as e:
            print(f"Error mantling {e}")

        #фігачим результати роботи по монтажу
        print("success:")
        for index, item in enumerate(success__description_logs['success'], start=1):
            print(f"    {index}. {item}")

        error_description =""
        print("errors:")
        for index, item in enumerate(success__description_logs['errors'], start=1):
            error_description =error_description + f"{item}\n\n"
            print(f"    {index}. {item}")
        if len(success__description_logs['errors']) == 0:
            error_description = "\n"

        formatted_message = (
            f"operation    : `{json2['Операція']}`\n"
            f"Назва          : `{json2['Марка']} {json2['Модель']} {json2['Номер']} {json2['Водитель']}`\n"
            f"Протокол   : `{protocol_name}`\n"
            f"EMEI            : `{json1['ИМЕИ']}`\n"
            f"shortEMEI    : `{json1['ИМЕИ'][-5:]}`\n"
            f"Cім               : `{sim}`\n\n"
            f"Errors:               : `{error_description}`\n"
            f"Дата заявки      :  `{readable_time}`\n"
            f"Підтвердження: `{formatted_datetime}`\n"
            f"Затримка          : `{delay}`\n"
            f"Ініціатор            :  `{json2['ініціатор']}`"
        )

        #видаляємо повідомлення і в чат пишем результат монтажу
        bot.send_message(call.message.chat.id, formatted_message, parse_mode="MarkdownV2", message_thread_id=THREAD_ID)
        bot.delete_message(call.message.chat.id, old_message_id)

# Функция для поиска текста кнопки по значению callback_data
def get_button_text_by_callback(callback_data, keyboard_data):
    for row in keyboard_data:
        for button in row:
            if button['callback_data'] == callback_data:
                return button['text']  # Возвращаем текст кнопки
    return None  # Если кнопка не найдена

@bot.message_handler(commands=['get_chat_id'])
@check_permissions
def get_chat_id(message):
    bot.send_message(message.chat.id, f"Your chat ID is: {message.chat.id} thread = {message.message_thread_id}",
                     message_thread_id=message.message_thread_id)


@bot.message_handler(commands=['start'])
@check_permissions
def start(message):
    chat_type = message.chat.type
    if chat_type == "private":
        bot.send_message(message.chat.id, "Доброго інженерного дня!", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data in ["yes", "no","confirm_dismantle","cancel","yes_find"
                                                            ,"show_dismantling","show_mantling"
                                                            ,"approve_dismantle","decline_dismantle"])
@check_permissions
def handle_callback(call):
    print(f"call data = {call.data}")

    user_id = call.from_user.id

    if call.data == "yes_find" and user_state[user_id].get("wialon_json"):
        print(user_state)
        for index, item in enumerate(user_state[user_id].get("wialon_json")):
            if index == 10: break
            bot.send_message(call.message.chat.id, f"```\n{json.dumps(item, indent=4, ensure_ascii=False)}\n```",
                             parse_mode="MarkdownV2")

    elif call.data == "show_dismantling":

        for index, item in enumerate(user_state[user_id].get("wialon_json")):
            if index == 10: break
            bot.send_message(call.message.chat.id, f"```\n{json.dumps(item, indent=4, ensure_ascii=False)}\n```",
                             parse_mode="MarkdownV2")

    elif call.data == "show_mantling":

        for index, item in enumerate(user_state[user_id].get("excell_json")):
            if index == 10: break
            bot.send_message(call.message.chat.id, f"```\n{json.dumps(item, indent=4, ensure_ascii=False)}\n```",
                             parse_mode="MarkdownV2")

    elif call.data == "yes" and user_state[user_id].get("wialon_json"):

        count_items = len(user_state[user_id].get("wialon_json"))
        if count_items > 1:
            for item in user_state[user_id].get("wialon_json"):
                bot.send_message(call.message.chat.id, f"```\n{json.dumps(item, indent=4, ensure_ascii=False)}\n```",
                                 parse_mode="MarkdownV2")
            bot.send_message(call.message.chat.id,
                             f"IMEI має бути унікальним, я зможу зробити демонтаж, якщо буде знайдено тільки один об'єкт")
            return

        #обнуляємо навігацію користувача (історію його виборів в меню)
        user_state.pop(user_id, None)
        engineer_gps_search_menu()

    elif call.data in ["no", "cancel"]:
        # обнуляємо навігацію користувача (історію його виборів в меню)
        user_state.pop(user_id, None)
        bot.send_message(call.message.chat.id, "Як забажаєте.",reply_markup=engineer_gps_menu())
        return

    #бот
    elif call.data == "confirm_dismantle":

        user_state.pop(user_id, None)
        message_text = call.message.text

        try:
            bot.send_message(ENGINEER_CHAT_ID, f"```\n{message_text}\n```" ,
                             parse_mode="MarkdownV2",
                             reply_markup=ask_approve_confirmation("approve_dismantle"),
                             message_thread_id=THREAD_ID)
        except Exception as e:
            bot.send_message(call.message.chat.id, f"Не знайдено чат з ID={ENGINEER_CHAT_ID} та THREAD_ID={THREAD_ID}")
            return

        # Удаляем сообщение в чате бота после отправки
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id,
                         f"```\n{message_text}\n```Демонтаж відправлено в основний чат",
                         parse_mode="MarkdownV2")

    #чат
    elif call.data == "approve_dismantle":
        print(f"User : {call.from_user.id} name = {call.from_user.first_name} "
              f"push '{call.data}' "
              f"Chat ID '{call.message.chat.id}' "
              f"message_thread_id = {getattr(call.message, 'message_thread_id', 'No thread ID')}")

        # Коли в чат падає заявка, то тільки адміністратор або власник може натиснути "Погодити"
        try:
            chat_member = bot.get_chat_member(call.message.chat.id, call.from_user.id)
            print(f"Role: {chat_member.status}")
            if chat_member.status not in ["administrator","creator"]:
                return
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Ошибка: {e}")
            bot.send_message(call.message.chat.id, f"Помилка ролі", message_thread_id=THREAD_ID)
            return

        # Зберігаємо  ідентифікатор старого повідомлення
        old_message_id = call.message.message_id

        #print(call.message.text)
        # конвертуэмо строку в словник
        message_dict = json.loads(call.message.text)
        # отримуэмо значення  "nm"
        #nm_value = message_dict.get("nm")
        # Получаем время отправки сообщения
        message_time = call.message.date

        # Преобразуем Unix timestamp в читаемый формат
        readable_time = datetime.fromtimestamp(message_time)
        #print(f"Value of 'nm': {nm_value}")

        # Отримуємо поточну дату та час
        current_datetime = datetime.now()
        # Форматуємо дату та час
        formatted_datetime = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
        # Вычисление разницы во времени
        delay = current_datetime - readable_time

        formatted_message = (
            f"operation    : `{message_dict.get('operation')}`\n"
            f"Назва          : `{message_dict.get('nm')}`\n"
            f"Протокол   : `{message_dict.get('protocol')}`\n"
            f"EMEI            : `{message_dict.get('uid')}`\n"
            f"shortEMEI    : `{message_dict.get('uid')[-5:]}`\n" 
            f"Cім               : `{message_dict.get('ph')[-10:]}`\n\n"
            f"Дата заявки      :  `{readable_time}`\n"
            f"Підтвердження: `{formatted_datetime}`\n"
            f"Затримка          : `{delay}`\n"
            f"Ініціатор            :  `{message_dict.get('creator')}`"
        )

        try:
            session = WialonManager(WIALON_URL, WIALON_TOKEN)
            #print(session._get_info())

            # Отримуємо об'єкт по EMEI
            my_json = session._get_list_universal("avl_unit",
                                            "sys_unique_id",
                                            f"*{message_dict.get('uid')}*",
                                            "sys_unique_id", 1, 1 + 256, 0, 10000)
            if not my_json['items']:
                print("не найдено EMEI")
                return
            id = my_json.get("items")[0].get("id")
            id_hv = my_json.get("items")[0].get('hw')
            #protocol = session._device_type(id_hv)

            #print(f"id = {id}")
            #print(f"id_hv = {id_hv}")
            #print(f"protocol = {protocol}")

            #обнуляємо EMEI та телефон. Протокол залишаємо
            session._update_protocol_imei(id,id_hv,"")
            session._update_phone(id, "")
            # дивимся в яких папках *Общая знаходиться обєкт і відправляємо в історію відповідно
            session._add_in_history(my_json.get("items")[0].get("id"))
            #видаляємо об'єкт з усіх основних групп крім *історія
            session._delete_obj_from_groups(id, "", "історія")
            print(f"Успішно видалений: {my_json.get("items")[0].get("nm")} ")
            print(my_json.get("items")[0])



        except telebot.apihelper.ApiTelegramException as e:
            print(f"Ошибка: {e}")

        bot.send_message(call.message.chat.id, formatted_message,parse_mode="MarkdownV2", message_thread_id=THREAD_ID)
        bot.delete_message(call.message.chat.id, old_message_id)

    elif call.data == "decline_dismantle":
        bot.delete_message(call.message.chat.id, call.message.message_id)

    # Закриваємо "завантаження" кнопки
    #bot.answer_callback_query(call.message.chat.id)

    # обнуляємо навігацію користувача (історію його виборів в меню)
    user_state.pop(user_id, None)
    print(f"Обнуляємо стан користувача: {user_state}")

    bot.answer_callback_query(call.id)

# оброботчик, для меню, який першим оброблюэ повідомлення від користувача
@bot.message_handler(func=lambda message: message.text in ['Вантажний автотранспорт', 'Комбайни'])
@check_permissions
def specific_handler(message):
    user_id = message.from_user.id
    user_state[user_id] = {'logistic_category': message.text}  # Зберігаємо вибрану категорію
    bot.send_message(message.chat.id, "Виберіть кластер:", reply_markup=logistic_inline_menu())
    #print(f"User ID: {user_id} вибрав : {message.text}\nUser State : {user_state}")

# оброботчик, для меню, який вибирає кластер
@bot.callback_query_handler(func=lambda call: call.data in ['ЧІМК', 'СА', 'АП', 'БА', 'АК', 'ІМК'])
@check_permissions
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

    # Удаляем состояние после выбора
    print(f"answer {generate_answer(category, cluster)}")
    try:
        session = WialonManager(WIALON_URL, WIALON_TOKEN)
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


@bot.message_handler(func=lambda message: message.chat.type ==  'private')
@check_permissions
def menu_handler(message):
    if message.text == 'Тест':
        bot.send_message(message.chat.id,  "Тестова ф-я завершилась", reply_markup=test_function(message))
        return
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
        bot.register_next_step_handler(message, find_function)

    elif message.text == 'По EMEI':
        bot.send_message(message.chat.id, "Введіть EMEI повністю або останні 4 цифри")
        bot.register_next_step_handler(message, find_emei_function)

    elif message.text == 'Демонтаж по EMEI':
        bot.send_message(message.chat.id, "Введіть EMEI повністю або частину:")
        bot.register_next_step_handler(message, dismantling_emei_equipment)

    elif message.text in ['Заміна SIM','Демонтаж по держ. номеру']:
        bot.send_message(message.chat.id, "В процесі розробки")

    elif message.text in 'Монтаж':
        bot.send_message(message.chat.id, "Введіть EMEI повністю або частину:")
        bot.register_next_step_handler(message, mantling_emei_equipment)

    elif message.text in 'Демонтаж':
        bot.send_message(message.chat.id, "Меню демонтажу", reply_markup=dismantling_gps_menu())

    elif message.text =='По SIM':
        bot.send_message(message.chat.id, "Вкажіть номер сімкарти для пошуку:\n Формат пошуку: 0671234567\n")
        bot.register_next_step_handler(message, find_sim_function)

    elif message.text == 'Ребут':
        bot.send_message(message.chat.id, "Починаю чистку історії переписки.")
        bot.send_message(message.chat.id, f"/start")

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
        print(message.chat.type)
        bot.send_message(message.chat.id, "Щось пішло не так.Повернення до головного меню", reply_markup=main_menu())

def find_emei_function(message):
    #якщо введено число
    if message.text.isdigit():
        bot.send_message(message.chat.id, "Ви ввели число. функція пошуку запущена")

        file_excel = ExcellLoader()
        json_list = file_excel.create_base_list()

        result = file_excel.find_emei(message.text, json_list)
        if len(result) > 5:
            bot.send_message(message.chat.id, f"Я знайшов {len(result)} ! \nВиведу тільки 1 результат де\n"
                                              f" {message.text} в кінці EMEI, якщо знайду такий."
                                              "\nСпробуйте ввести на одну цифру більше для уточнення")
        result_json = {"Excell":result[:1]}
        bot.send_message(message.chat.id, f"```\n{json.dumps(result_json, indent=4, ensure_ascii=False)}\n```",parse_mode="MarkdownV2")

    else:
        bot.send_message(message.chat.id, "Ви ввели не число а якусь беліберду.")

def mantling_emei_equipment(message):

    if message.text.isdigit():
        #bot.send_message(message.chat.id, "Ви ввели число. Починаю пошук")
        text2 = {
            "Операція": "",
            "Кластер": "",
            "Власність": "",
            "Група": "",
            "Підгрупа": "",
            "Марка": "",
            "Модель": "",
            "Номер": "",
            "Водитель": "",
            "ініціатор": ""
        }
        try:
            file_excel = ExcellLoader()
            json_list = file_excel.create_base_list()

            result = file_excel.find_emei(message.text, json_list)


            for item in result:
                del item["Склад"]
            #print(json.dumps(result, indent=4, ensure_ascii=False))


            if len(result) > 1:
                ask_confirmation(message, len(result),
                                 "\nЯ зможу зробити монтаж тільки в тому випадку, коли EMEI унікальний.\n"
                                 "Інакше виведу результат пошуку але не більше 10!", "mantling")
                user_state[message.from_user.id] = {
                    'excell_json': result}  # Зберігаємо list_json в словник станів

            if len(result) == 1:

                #Перевіряємо чи є такий емей у Віалоні
                try:
                    info_wialon = WialonManager(WIALON_URL,WIALON_TOKEN)
                    #Перевіряэмо наявність EMEI у Wialon
                    id = info_wialon._get_id_from_uid(result[0].get('ИМЕИ'))
                    print(id)
                    if id:
                        #Якщо є то виводимо в бот інформацію про цей обєкт з EMEI і завершуємо процедуру монтажу
                        print(info_wialon._get_info_from_telegram(id))
                        bot.send_message(message.chat.id,
                                         f"```\n{json.dumps(info_wialon._get_info_from_telegram(id),
                                                            indent=4, ensure_ascii=False)}\n"
                                         f"```Я не можу провести зробити монтаж, бо такий IMEI уже є в Wialon",
                                         parse_mode="MarkdownV2")
                        return

                except Exception as e:
                    bot.send_message(message.chat.id,f"Сталася помилка пошуку EMEI у Віалоні: {e}")
                    return


                formatted_text = (f"```\n{json.dumps(result[0], indent=4, ensure_ascii=False)}\n```\n"
                                  f"\n```\n{json.dumps(text2, indent=4, ensure_ascii=False)}\n```")

                #Виводим заготовку по монтажу в бот з потрібною inline клавіатурою
                keyboard = mantle_stage_1_inline_keyboard()
                bot.send_message(
                                    message.chat.id,
                                    formatted_text,
                                    parse_mode = "MarkdownV2",
                                    reply_markup=keyboard
                                 )

            if len(result) == 0:
                bot.send_message(message.chat.id, "Я нічого не знайшов. Спробуйте ще раз")
                return


        except Exception as e:
            print(f"Сталася помилка: {e}")


    else:
        bot.send_message(message.chat.id, "Ви ввели не число а якусь беліберду.")

def dismantling_emei_equipment(message):
    if message.text.isdigit():
        bot.send_message(message.chat.id, "Ви ввели число. Починаю пошук")

        try:
            session = WialonManager(WIALON_URL,WIALON_TOKEN)
            print(f"{message.from_user.id} create session:\n{session._get_info()}")


            myjson = session._get_json_uid_for_emei(message.text)
            count_obj = len(myjson["wialon"])
            print(f"Найдено {count_obj} об'єктів")

            if len(myjson["wialon"]) >1:
                ask_confirmation(message, count_obj, "\nЯ зможу зробити демонтаж тільки в тому випадку, коли EMEI унікальний.\n"
                                                     "Інакше виведу результат пошуку але не більше 10!","dismantling")
                user_state[message.from_user.id] = {
                    'wialon_json': myjson["wialon"]}  # Зберігаємо list_json в словник станів

            if len(myjson["wialon"]) ==1:
                myjson["wialon"][0] = {"operation": "демонтаж", "creator": message.from_user.username, **myjson["wialon"][0] }
                bot.send_message(message.chat.id,
                                 f"```\n{json.dumps(myjson["wialon"][0], 
                                    indent=4, ensure_ascii=False)}\n```",
                                     parse_mode = "MarkdownV2",
                                 reply_markup=ask_approve_confirmation("confirm_dismantle"))

                user_state[message.from_user.id] = {
                    'wialon_json': myjson["wialon"]}  # Зберігаємо list_json в словник станів

            if len(myjson["wialon"]) ==0:
                bot.send_message(message.chat.id, "Я нічого не знайшов. Спробуйте ще раз")

        except Exception as e:
            print(f"Сталася помилка: {e}")


    else:
        bot.send_message(message.chat.id, "Ви ввели не число а якусь беліберду.")

def find_sim_function(message):
    # якщо введено число
    if message.text.isdigit():
        bot.send_message(message.chat.id, "Ви ввели номер телефону. функція пошуку запущена")

        file_excel = ExcellLoader()
        json_list = file_excel.create_base_list()

        result = file_excel.find_sim(message.text, json_list)
        print(result)
        if len(result) > 5:
            bot.send_message(message.chat.id, f"Я знайшов {len(result)} і виведу тільки 1 результат де\n"
                                              f" {message.text} є в полі Sim'."
                                              "\nСпробуйте ввести на одну цифру більше для уточнення")
        result_json = {"Excell":result[:1]}
        bot.send_message(message.chat.id, f"```\n{json.dumps(result_json, indent=4, ensure_ascii=False)}\n```",
                         parse_mode="MarkdownV2")

def find_function(message):

    if message.text == "<-Назад":
        bot.send_message(message.chat.id, "Повернення до меню", reply_markup=engineer_gps_menu())
    if message.text in ["По EMEI", "По SIM", "По держ. номеру"]:
        bot.send_message(message.chat.id, "Ви не ввели держ. номер вручну!\nВиберіть знову критерій пошуку.")
        return
    plate_number = message.text.strip().upper()
    bot.send_message(message.chat.id, f"Ви ввели держ. номер = {plate_number}")

    # тут перевіряємо на правильність держномера
    if (plate_number == "ALL" or
            (len(plate_number) == 8 and
             plate_number[:2].isalpha() and
             plate_number[2:6].isdigit() and
             plate_number[6:].isalpha()) or
            (len(plate_number) == 7 and
             plate_number[:5].isdigit() and
             plate_number[5:].isalpha())):
        bot.send_message(message.chat.id, f"Держ номер {plate_number} прийнято!")


        session = WialonManager(WIALON_URL, WIALON_TOKEN)
        #print(session._get_info())


        my_json = session._get_list_universal("avl_unit",
                                              "sys_name",
                                              f"*{plate_number}*",
                                              "sys_name", 1, 1 + 256 + 1024 + 4096 + 2097152, 0, 10000)

        if len(my_json['items']) == 0:
            bot.send_message(message.chat.id, f"Вибачте, я не знайшов такого держ.номера")
            main_menu()
            return
        ask_confirmation(message,len(my_json['items']),"", "find")

        user_state[message.from_user.id] = {'wialon_json': session._get_special_list_json(my_json)}  # Зберігаємо list_json в словник станів
        #print(f"user state = \n{json.dumps(user_state[message.from_user.id], indent=4, ensure_ascii=False)}")

    else:
        bot.send_message(message.chat.id, "Невірний формат." ,reply_markup=engineer_gps_search_menu())

def generate_answer(category, cluster):
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
