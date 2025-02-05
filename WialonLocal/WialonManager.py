import json
from cgitb import reset
from datetime import datetime, timezone, timedelta

from typing import Dict

from numpy.ma.core import empty
from shapely.geometry import Polygon
from unicodedata import category
from webbrowser import Error

import pytz
from turtledemo.clock import datum

import pytz
import requests
from oauthlib.uri_validate import query
from openpyxl.descriptors import String

from WialonLocal.WialonAuth import login
class WialonManager:

    def __init__(self, base_url,token):
        """ конструктор класу
        """
        self.__base_url = base_url
        self.__token = token
        self.__sid = self.__get_sid()


        if not self.__sid:
            raise Exception("Не вдалося залогінитися! Немає sid.")

    def __get_sid(self):
        login_url = f"{self.__base_url}/wialon/ajax.html?svc=token/login&params={{\"token\":\"{self.__token}\"}}"
        response = requests.get(login_url)
        sid = None
        # Перевірка результату
        if response.status_code == 200:
            #print("Успішно залогінився")
            data = response.json()
            sid = data.get('eid')  # Токен сесії
            #print("sid = ", sid)
        else:
            raise Exception(f"Не вдалося залогінитися! Немає sid.{response.status_code}")
        return sid

    def _get_info(self):
        return f"URL = {self.__base_url}\nTOKEN = {self.__token}\nsid = {self.__sid}"

    def _print_json_result(self,data):
        units = data.get('items', [])
        for unit in units:
            print(f"ID: {unit.get('id')}, Назва: {unit.get('nm')}")

    def _get_json_str(self,data):
        """
        Дана функція повертає Json у строці в гарному вигляді для виводу в консоль
        :param data: Json
        :return: str
        """
        return json.dumps(data, indent=4, ensure_ascii=False)

    def _get_list_from_mask(self,mask):
        """
        Функція пошуку об'єктів в назві по заданій масці
        :param mask: маска пошуку об'єктів по назві
        :return: json
        """
        query = (
            'svc=core/search_items&params={"spec":{'
            '"itemsType":"avl_unit",'
            '"propName":"sys_name",'
            f'"propValueMask":"*{mask}*",'
            '"sortType":"sys_name"'
            '},'
            '"force":1,'
            '"flags":1,'
            '"from":0,'
            '"to":10000'
            '}'
        )
        response = requests.get(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")
        data = response.json()
        return data

    def _update_group(self,group_id,list_id):
        """
        Функція апдейту об'єктів в групі
        :param group_id: маска пошуку групи по ID
        :return: json
        """
        query = (
            'svc=unit_group/update_units&params={'
            f'"itemId":"{group_id}",'
            f'"units":{list_id}'
            '}'
        )
        response = requests.get(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")
        data = response.json()
        return data

    def _find_groups(self,group_mask_name="*",exception_name_mask="!*історія*", creator_id="145|47|163|249|368",flags=7):
        """
        Фцнкція повертає групи техніки за заданими критеріями

        :param group_mask_name: Маска імені групи. Приклад: *Вантажні*
        :param exception_name_mask: Маска виключень в імені групи. Приклад: не відображати "!*історія*"
        :param creator_id: ID творця. Приклад: "145|47|163|249|368"
        :param flags:  Флаг виводу
        :return: json
        """
        query = (
            'svc=core/search_items&params={"spec":{'
            '"itemsType": "avl_unit_group",'
            '"propName": "sys_name,sys_name,sys_user_creator",'
            f'"propValueMask": "{group_mask_name},{exception_name_mask},{creator_id}",'
            '"sortType": "sys_units",'
            '"propType": "sys_name,sys_user_creator",'
            '"or_logic": "0"'
            '},'
            '"force": "1",'
            f'"flags": "{flags}",'
            '"from": "0",'
            '"to": "100000"'
            '}'
        )

        response = requests.get(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")
        data = response.json()
        return data


    def _add_obj_to_group(self,obj_id,group_name):
        """
        Шукаємо по групі точне співпадіння назви групи. Творці групи повинні мати id ="145|47|163|249|368"
        Отримуємо список id обєктів, додаємо новий obj_id та робимо апдейт групи
        :param obj_id:
        :param group_name:
        :return: [Not added. Found more than 1 group,
                    already added,
                    sucsess,
                    none]

        """
        result = self._find_groups(group_name)['items']
        if len(result) > 1:
            return "Not added. Found more than 1 group"
        if not result: return "Not found group"

        for item in result:
            if group_name == item['nm']:
                #перевіряєм об'єкт в групі
                if obj_id in item['u']:
                    return "already added"

                temp_list = item['u']
                temp_list.append(obj_id)
                temp_list.sort()
                self._update_group(item['id'],temp_list)
                return "sucsess"

        return "none"

    def _delete_obj_from_groups(self,id_obj, name_group, exception_name_group ):
        """
        Дана функція отримує список груп в якій знаходиться об'єкт по id. робимо апдейт груп і виключаємо id об'єкта
        із списка даної групи

        :param id_obj: id об'єкта що хочемо видалить з груп
        :param name_group: Макса групп. Якщо name_group="", то видаляється з усіх крім exception_name_group
        :param exception_name_group: виключення з яких груп не видаляємо об'єкт. Приклад exception_name_group="історія"
        :return: json
        """
        #Шукаємо всі групи, в яких знаходиться id_obj
        json_result = self._find_group_for_id_obj(id_obj)

        #якщо маска групи пуста то видаляєм з усіх груп
        if name_group=="":
            for item in json_result["items"]:
                #пропускаємо виключення по назві групи
                if exception_name_group in item["nm"]:
                    continue
                if id_obj in item["u"]:
                    #видаляємо id об'єкта з списка та робимо апдейт списка групи з id
                    item["u"].remove(id_obj)
                    self._update_group(item["id"],item["u"])

        else:
            for item in json_result["items"]:
                #пропускаємо виключення по назві групи
                if exception_name_group in item["nm"]:
                    continue
                if name_group == item["nm"]:
                    if id_obj in item["u"]:
                        # видаляємо id об'єкта з списка та робимо апдейт списка групи з id
                        item["u"].remove(id_obj)
                        self._update_group(item["id"],item["u"])


        return json_result

    def _find_group_for_id_obj(self, obj_id):

        json_result = self._find_groups("*", "**", "145|47|163|249|368", 7)

        #цикл із зворотньою ітерацією, щоб не порушить індекси при видаленні елементів:
        for index in range(len(json_result["items"]) - 1, -1, -1):
            if obj_id not in json_result["items"][index]["u"]:
                del json_result["items"][index]  # Видаляємо елемент по index

        return json_result

    def _get_list_universal(self, itemsType: object, propName: object, propValueMask: object, sortType: object, force: object, flags: object, _from: object, to: object) -> object:
        """
        Універсальна ф-кція пошуку елементів в Wialon Local
        :param itemsType: тип шуканих елементів (див. список нижче), якщо залишити порожнім, то пошук здійснюватиметься за всіма типами
        :param propName:ім'я властивості, за якою здійснюватиметься пошук (див. список можливих властивостей нижче):може бути використаний |
        :param propValueMask: значення властивості: можуть бути використані * | , > < = =
        :param sortType: ім'я властивості, за якою буде здійснюватися сортування відповіді
        :param force: 0 - якщо такий пошук уже запитувався, то поверне отриманий результат, 1 - шукатиме заново
        :param flags: флаг
        :param _from: від
        :param to: до
        :return: json
        """
        query = (
            'svc=core/search_items&params={"spec":{'
            f'"itemsType":"{itemsType}",'
            f'"propName":"{propName}",'
            f'"propValueMask":"{propValueMask}",'
            f'"sortType":"{sortType}"'
            '},'
            f'"force":{force},'
            f'"flags":{flags},'
            f'"from":{_from},'
            f'"to":{to}'
            '}'
        )

        response = requests.get(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")
        data = response.json()
        return data

    def _get_json_uid_for_emei(self, emei : str) -> Dict:
        """
        Функція повертає список uid по заданому EMEI
        :param emei: 0 < emei < 15 - емей gps обладнання
        :return: Dict [wialon][Dict]
        """
        json = self._get_list_universal("avl_unit",
                                              "sys_unique_id",
                                              f"*{emei}*",
                                              "sys_unique_id", 1, 1 +256 , 0, 10000)

        list ={
            "wialon" : []
        }

        for index, item in enumerate(json["items"]):
            """list["wialon"][index+1] = {
                'nm' : item['nm'],
                'uid' : item['uid'],
                'ph' : item['ph']
            }"""
            list["wialon"].append({
                'nm' : item['nm'],
                'protocol' : self._device_type(item['hw']),
                'uid' : item['uid'],
                'ph' : item['ph'],
                'id' : item['id']
            })
        return list

    def _get_list_uid_for_groupName(self,gropName):
        """
        Фукнція повертає List з uid об'єктів, що знаходяться в групі з назвою propName
        :param gropName: назва групи
        :return: list[uid1, uid2, uid3...]
        """
        json = self._get_list_universal("avl_unit_group",
                                       "sys_name,sys_id,sys_unique_id",
                                       gropName,
                                       "sys_name", 1, 1  + 256 + 1024+ 4096 + 2097152, 0, 10000)
        return json["items"][0]['u']

    def _get_json_for_groupName(self,gropName):
        """
        Фукнція повертає List з uid об'єктів, що знаходяться в групі з назвою propName
        :param gropName: назва групи
        :return: list[uid1, uid2, uid3...]
        """
        json = self._get_list_universal("avl_unit_group",
                                       "sys_name,sys_id,sys_unique_id",
                                       gropName,
                                       "sys_name", 1, 1  + 256 + 1024+ 4096 + 2097152, 0, 10000)
        return json

    def _get_obj_for_id(self, obj_id):

        query = (
            'svc=core/search_item&params={'
            f'"id":{obj_id},'
            f'"flags":{1+128+4096}'
            '}'
        )

        response = requests.get(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")
        data = response.json()
        return data

    def _get_name_obj_for_device_phone(self, phone):
        """
        Пошук об'єкта за вказаним номером телефону трекера
        :param phone:
        :return: 'nm' or "Not found"
        """
        query = (
            'svc=core/search_items&params={"spec":{'
            '"itemsType": "avl_unit",'
            '"propName": "sys_phone_number",'
            f'"propValueMask": "{phone}",'
            f'"sortType": "avl_unit",'
            '"propType": "sys_phone_number",'
            '"or_logic": "0"'
            '},'
            '"force": "1",'
            f'"flags": "1",'
            '"from": "0",'
            '"to": "100000"'
            '}'
        )


        response = requests.get(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")

        data = response.json()
        if not data["items"]: return "Not found"
        return data["items"][0]["nm"]

    def _get_obj_for_id_and_flags(self, obj_id:int, flags:int):
        """
        Отримати об'єкт за id та flags
        :param obj_id: id об'єкта
        :param flags: флаг об'єкта
        :return: json
        """
        query = (
            'svc=core/search_item&params={'
            f'"id":{obj_id},'
            f'"flags":{flags}'
            '}'
        )

        response = requests.get(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")
        data = response.json()
        return data

    def _get_all_sensors(self,obj):
        sensors_list = []
        # Проход по всем сенсорам и вывод их имен
        for sensor_id, sensor_data in obj["item"]["sens"].items():
            sensors_list.append(sensor_data["n"])
        return sensors_list

    def _get_sensor_value(self,obj_id):
        query = (
            'svc=unit/calc_last_message&params={'
            f'"unitId":{obj_id}'
            '},'
            f'"sensors": {[]}'
            '}'
        )
        response = requests.get(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")
        data = response.json()
        return data

    def _create_obj(self, creatorId:str, name:str, hwTypeId:str):
        query = (
            'svc=core/create_unit&params={'
            f'"creatorId":"{creatorId}",'
            f'"name":"{name}",'
            f'"hwTypeId":"{hwTypeId}",'
            f'"dataFlags":"1"'
            '}'
        )

        response = requests.get(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")
        data = response.json()

        return data

    def _create_my_json(self,gropName):
        data = {
            "items": {}
        }

            #отримать всі uid що в групі і загнать їх в ліст list_uid
        list_uid = self._get_list_uid_for_groupName(gropName)
        #print(json.dumps(list_uid, indent=4, ensure_ascii=False))

        for index, uid in enumerate(list_uid):

            obj = self._get_obj_for_id(uid)  # Получаем объект по UID

            sensors = obj.get("item", {}).get("sens", {})

            data["items"][str(index + 1)] = {  # Індекси в json починаються з 0, тому добавляємо 1
                "id": obj.get("item").get("id"),
                "nm": obj.get("item").get("nm"),
                "sensors": self.__parse_sensors(obj.get("item").get("id"), sensors),
                "property": self.__find_aflds_property(obj, "Власність")
            }
            print(data["items"][str(index + 1)])

        return data

    def __parse_sensors(self, id_obj,sensors):
        sensors_map ={}

        for sensor_id, sensor_data in sensors.items():
            sensors_map[sensor_data.get('n')] = self._get_sensor_value(id_obj).get(sensor_id)
        return sensors_map

    #повертає назву протоколу(обладнання) по id
    def _device_type(self,id_device : int) -> str :

        query = (
            'svc=core/get_hw_types&params={'
            f'"filterType":"id",'
            f'"filterValue":[{id_device}],'
            f'"includeType":0,'
            f'"ignoreRename":1'
            '}'
        )

        response = requests.get(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")
        data = response.json()
        for device in data:
            if device['id'] == id_device:
                return device['name']
        else:
            return "Device not found"

    def _get_device_id_and_type(self,mask_name="all"):
        """
        Функція повертає список id та name протоколів за вказаною маскою
        :param mask_name: Мака імені протокола. По замовчуванню поверне ввесь список з усіма атрибутами
        :return: list
        """
        query = (
            'svc=core/get_hw_types&params={'
            f'"filterType":"id",'
            f'"filterValue":{1},'
            f'"includeType":0,'
            f'"ignoreRename":1'
            '}'
        )

        response = requests.get(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")
        data = response.json()
        if mask_name == "all":
            return data
        filtered_list = [{"id": item["id"], "name": item["name"]} for item in data if mask_name in item.get("name")]
        return filtered_list

    def _get_users_from_mask(self, mask_name=""):


        query = (
            'svc=core/search_items&params={"spec":{'
            f'"itemsType":"user",'
            f'"propName":"sys_name",'
            f'"propValueMask":"*{mask_name}*",'
            f'"sortType":"sys_name"'
            '},'
            f'"force":"1",'
            f'"flags":"1",'
            f'"from":"0",'
            f'"to":"100000"'
            '}'
        )

        response = requests.get(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")
        data = response.json()
        return data

    def __find_aflds_property(self,data,key_property):
        """
        Дізнаємось хто власник об'єкта, якщо це вказано в адміністративному полі об'єкта. Пошук за ключем
        :param data: об'єкт
        :param key_property: ключ пошуку в адміністративних полях
        :return: string
        """
        aflds = data.get("item", {}).get("aflds", {})
        result = {}

        for key, value in aflds.items():
            if value.get("n") == key_property:
                result[value.get("n")] = value.get("v")

        return result

    def _simple_query_str(self,query):
        response = requests.get(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")
        data = response.json()
        print(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")
        return self._get_json_str(data)

    def _get_special_list_json(self, my_json):

        result_list = []

        for i, item in enumerate(my_json['items']):
            #print(f"Index {i+1}: {item['nm']}")
            try:
                last_msg_utc_time = datetime.fromtimestamp(my_json['items'][i]['lmsg']['t'], timezone.utc)
                # Переврдимо дату по Києву (автоматично)
                last_msg_utc_time = last_msg_utc_time.astimezone(pytz.timezone('Europe/Kyiv'))
            except Exception as e:
                print(f"Помилка отримання дати в _get_special_list_json {e}")
                last_msg_utc_time = None
            # отримуємо значення всіх датчиків по id об'єкта - id sensors: value
            sensor_value_list = self._get_sensor_value(my_json['items'][i]['id'])
            # вивантажуємо в ліст назву датчика та останні його значення якщо це датчики напруги
            sensors_data = []
            for id, n in my_json['items'][i]['sens'].items():
                if n['n'] in ['Заряд батареї', 'Зовнішня напруга']:
                    sensors_data.append(f"{n['n']} : {sensor_value_list[id]}")
            data = {
                # "id": my_json['items'][i]['id'],
                "name": my_json['items'][i]['nm'],
                "protocol": self._device_type(my_json['items'][i]['hw']),
                "emei": my_json['items'][i]['uid'],
                "sim": my_json['items'][i]['ph'],
                "online": my_json['items'][i]['netconn'],
                "time": last_msg_utc_time.strftime("%Y-%m-%d %H:%M:%S") if last_msg_utc_time != None else "None",
                "sensors": sensors_data
            }
            result_list.append(data)

        return result_list

    def _update_protocol_imei(self,id_obj,id_hv,id_uid):

        query = (
            'svc=unit/update_device_type&params={'
            f'"itemId":{id_obj},'
            f'"deviceTypeId":{id_hv},'
            f'"uniqueId":"{id_uid}"'
            '}'
        )
        response = requests.get(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")
        data = response.json()
        return data

    def _update_protocol_password(self,id_obj,password=""):
        """
        Змінити пароль до протоколу
        :param id_obj:
        :param password:
        :return: {'psw': '<long>'}
        """
        query = (
            'svc=unit/update_access_password&params={'
            f'"itemId":{id_obj},'
            f'"accessPassword":{password}'
            '}'
        )
        response = requests.get(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")
        data = response.json()
        return data

    def _update_phone(self,id_obj,phone:str):

        query = (
            'svc=unit/update_phone&params={'
            f'"itemId":{id_obj},'
            f'"phoneNumber":"{phone}"'
            '}'
        )
        response = requests.get(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")
        data = response.json()
        return data

    def _get_id_from_uid(self, uid):
        """
        Вказуємо точний uid і отримуємо id об'экта
        :param uid: EMEI
        :return: id obj
        """
        query = (
            'svc=core/search_items&params={"spec":{'
            f'"itemsType":"avl_unit",'
            f'"propName":"sys_unique_id",'
            f'"propValueMask":"{uid}",'
            f'"sortType":"sys_unique_id"'
            '},'
            f'"force":{1},'
            f'"flags":{1},'
            f'"from":{0},'
            f'"to":{10000}'
            '}'
        )

        response = requests.get(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")
        data = response.json()
        if not data.get('items'): return None
        return data.get('items')[0].get('id')

    def _get_geofences(self,id_creators="*145|47|163|249|368*"):
        """
        Функція повертає json з усіма полями в основних ресурсах, де id ресурсів можна передати.
        :param id_creators: id ресурсів де знаходяться основні поля (чи юзерів чи ресурсів уточнити)
        :return: json
        """
        query = (
            'svc=core/search_items&params={'
            '"spec":{'
                '"itemsType":"avl_resource",'
                '"propName":"zones_library,sys_user_creator",'
                f'"propValueMask":"**,{id_creators}",'
                '"sortType":"zones_library",'
                '"propType":"propitemname"'
                '},'
            '"force":"1",'
            '"flags":"4097",'
            '"from":"0","to":"100000"'
            '}'
        )

        response = requests.get(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")
        data = response.json()
        return data

    def _get_geofense_ifo(self,resourse_id,geofence_id):
        """
        Отримуємо дані геозон по ID ресурса та list[] з ID полів
        :param resourse_id:
        :param geofence_id:
        :return:
        """
        query = (
            'svc=resource/get_zone_data&params={'
            f'"itemId":"{resourse_id}",'
            '"col":"",'
            '"flags":"28"'
            '}'
        )
        response = requests.get(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")
        data = response.json()
        return data

    def _get_id_from_name_resource(self,name_resource:str):
        """
        Функція повертає ID ресурса

        :param name_resource: ім'я ресурса
        :return: id
        """
        query = (
            'svc=core/search_items&params={'
            '"spec":{'
            '"itemsType":"avl_resource",'
            '"propName":"sys_name",'
            f'"propValueMask":"{name_resource}",'
            '"sortType":"sys_name"'    
            '},'
            '"force":"1",'
            '"flags":"1",'
            '"from":"0","to":"100000"'
            '}'
        )
        response = requests.get(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")
        data = response.json()
        return data.get("items")[0].get('id')

    def _get_user_id(self,user_name):
        """
        Отримуємо ID User за ім'ям
        :param user_name: ім'я користувача
        :return: id:int
        """
        query = (
            'svc=core/search_items&params={'
            '"spec":{'
            '"itemsType": "user",'
            '"propName":"sys_name",'
            f'"propValueMask":"{user_name}",'
            '"sortType":"sys_name"'
            '},'
            '"force":"1",'
            '"flags":"1",'
            '"from":"0","to":"100000"'
            '}'
        )

        response = requests.get(f"{self.__base_url}/wialon/ajax.html?{query}&sid={self.__sid}")
        data = response.json()
        return data.get('items')[0].get('id')

    def _get_not_valid_geofences_list(self, name_resource:str):
        """
        Функція повертає json де вказано список полів з неправильними геометричними контурами
        :param name_resource: ім'я ресурсу
        :return: json
        """
        def is_valid_contour(points):
            # Преобразуем список точек в замкнутую последовательность
            points = [(p['x'], p['y']) for p in points]
            points.append(points[0])  # Замкнем контур

            # Создаем многоугольник из точек
            polygon = Polygon(points)

            # Проверяем, является ли этот многоугольник валидным
            if polygon.is_valid:
                return True
            else:
                return False

        json = {
            "name": name_resource,
            "count_geofences": None,
            "valid": None,
            "not_valid": None,
            "list_not_valid": []
        }

        id = self._get_id_from_name_resource(name_resource)

        count_valid = 0
        list_no_valid = []
        json["count_geofences"] =len(self._get_geofense_ifo(id,""))
        for item in self._get_geofense_ifo(id,""):
            #print(f"id = {item['id']}  name = {item['n']}  p = {item['p']}")
            is_valid = is_valid_contour(item['p'])
            if is_valid: count_valid = count_valid + 1
            if not is_valid: list_no_valid.append(item['n'])


        json["valid"] = count_valid
        json["not_valid"] = len(list_no_valid)
        json["list_not_valid"] = list_no_valid

        return json

    def _get_info_from_telegram(self,obj_id):
        """
        Функція повертає інформацію про об'єкт за obj_id
        :param obj_id:
        :return: json
        """

        json = {
            "name" : "null",
            "protocol" : "null",
            "IMEI" : "null",
            "phone" : "null",
            "last msg" : "null",
            "groups": []
        }
        obj = self._get_obj_for_id_and_flags(obj_id, 1 + 256 + 1024)
        json['name'] = self._get_obj_for_id_and_flags(obj_id, 1 + 256).get("item").get('nm')
        json['IMEI'] = self._get_obj_for_id_and_flags(obj_id, 1 + 256).get("item").get('uid')
        json['protocol'] = self._device_type(self._get_obj_for_id_and_flags(obj_id, 1 + 256).get("item").get('hw'))
        json['phone'] = self._get_obj_for_id_and_flags(obj_id, 1 + 256).get("item").get('ph')
        for item in self._find_group_for_id_obj(obj_id).get('items'):
            json['groups'].append(item.get('nm'))

        try:
            last_msg_utc_time = datetime.fromtimestamp(obj['item']['lmsg']['t'], timezone.utc)
            # Переврдимо дату по Києву (автоматично)
            last_msg_utc_time = last_msg_utc_time.astimezone(pytz.timezone('Europe/Kyiv'))
            json['last msg'] = last_msg_utc_time.strftime("%Y-%m-%d %H:%M:%S") if last_msg_utc_time != None else "None"
        except Exception as e:
            print(f"Помилка отримання дати в _get_special_list_json {e}")
            json['last msg'] = last_msg_utc_time.strftime("%Y-%m-%d %H:%M:%S") if last_msg_utc_time != None else "None"

        return json

    def _add_in_history(self,obj_id):
        """
        Якщо обєкт знаходиться в групі ЧІМК общая, то цей id обєкту добавляється в групу ЧІМК історія.
        Відповідна дія і до інших кластерів
        :param obj_id:
        :return:
        """
        list_update = {
            'added' : []
        }
        # Пробігаємось по всім основним групам в яких знаходиться obj_id
        for item in self._find_group_for_id_obj(obj_id).get('items'):
            # Якщо група має назву 'АП Общая'
            if item['nm'] == 'АП Общая':
                # отримуємо перелік об'єктів що знаходяться в групі АП історія
                list_uid =self._get_list_uid_for_groupName("АП історія")
                # Якщо обєкт з obj_id  нема в списку то добавляємо його в список
                if obj_id not in list_uid: list_uid.append(obj_id)
                # Робимо сортування списку на всякий випадок
                list_uid.sort()
                # Оновлюємо в групі спикок обєктів. Дуже страшна дія але шо робить.
                self._update_group(1088, list_uid)
                list_update['added'].append("АП історія")

            if item['nm'] == 'ЧІМК Общая':
                list_uid = self._get_list_uid_for_groupName("ЧІМК історія")
                if obj_id not in list_uid: list_uid.append(obj_id)
                list_uid.sort()
                self._update_group(1359, list_uid)
                list_update['added'].append("ЧІМК історія")
            if item['nm'] == 'АК Общая':
                list_uid = self._get_list_uid_for_groupName("АК історія")
                if obj_id not in list_uid: list_uid.append(obj_id)
                list_uid.sort()
                self._update_group(1058, list_uid)
                list_update['added'].append("АК історія")
            if item['nm'] == 'СА Общая':
                list_uid = self._get_list_uid_for_groupName("СА історія")
                if obj_id not in list_uid: list_uid.append(obj_id)
                list_uid.sort()
                self._update_group(1232, list_uid)
                list_update['added'].append("СА історія")
            if item['nm'] == 'БА Общая':
                list_uid = self._get_list_uid_for_groupName("БА історія")
                if obj_id not in list_uid: list_uid.append(obj_id)
                list_uid.sort()
                self._update_group(1150, list_uid)
                list_update['added'].append("БА історія")

        return list_update

    def _get_id_and_pass_protocol_for_user_mask(self,mask) :
        """
        Ця функція чисто користувацька за власними правилами узгодженими адміністратором.
         Вказуємо назву протоколу із 1С і отримуємо id протокола з Wialon Local та умовно прийнятий стандартиний пароль
         до цього протоколу

        :param mask: "810 Connect" - так підписано трекер в 1С
        :return: [23,"1111"] - де id = 23 та pass = 1111
        """
        # Wialon IPS = 23
        # Bitrek = 10
        # BI 810 TREK = 14
        # BI 920 TREK = 11
        # BI 820 TREK OBD = 8
        # BI 910 TREK = 15
        # BI 530R TREK = 1956

        if mask == "FMS 500 Tacho SDK": return [3183,""]
        if mask == "810": return [14,""]
        if mask == "810 Connect": return [23,"1111"]
        if mask == "820 OBD": return [8,""]
        if mask == "910": return [15,""]
        if mask == "920": return [11,""]
        if mask == "BI 530C TREK": return [23,"1111"]
        if mask == "BI 530R TREK": return [1956,"1111"]
        if mask == "BI868 V10 TREK": return [23,"1111"]
        if mask == "FMA120": return [10,""]
        else: return [23,""]





















