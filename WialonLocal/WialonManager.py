import json
from http.client import responses
import requests
from oauthlib.uri_validate import query
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

    def _get_list_universal(self,itemsType,propName,propValueMask,sortType,force,flags,_from,to):
        """
        Універсальна ф-кція пошуку
        :param mask: маска пошуку об'єктів по назві
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

    def _get_list_uid_for_groupName(self,gropName):
        """
        Фукнція повертає List з uid об'єктів, що знаходяться в групі з назвою propName
        :param gropName: назва групи
        :return: list[uid1, uid2, uid3...]
        """
        json = self._get_list_universal("avl_unit_group",
                                       "sys_name,sys_id,sys_unique_id",
                                       gropName,
                                       "sys_name", 1, 1, 0, 10000)
        # Достаем значение поля 'u'
        u_values = json['items'][0]['u']
        return u_values

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

    def _create_my_json(self,gropName):
        data = {
            "items": {}
        }

        #отримать всі uid що в групі і загнать їх в ліст list_uid
        list_uid = self._get_list_uid_for_groupName(gropName)

        for index, uid in enumerate(list_uid):
            obj = self._get_obj_for_id(uid)  # Получаем объект по UID
            sensors = obj.get("item", {}).get("sens", {})
            data["items"][str(index + 1)] = {  # Індекси в json починаються з 0, тому добавляємо 1
                "id": obj.get("item").get("id"),
                "nm": obj.get("item").get("nm"),
                "sensors":self.__parse_sensors(obj.get("item").get("id"),sensors),
                "property": self.__find_aflds_property(obj, "Власність")
            }


        return data

    def __parse_sensors(self, id_obj,sensors):
        sensors_map ={}

        for sensor_id, sensor_data in sensors.items():
            sensors_map[sensor_data.get('n')] = self._get_sensor_value(id_obj).get(sensor_id)
        return sensors_map

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

