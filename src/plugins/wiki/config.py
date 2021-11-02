import json
import os
from pathlib import Path

WIKI_DIR = Path(".") / "data" / "database" / "wiki"


class NoDefaultPrefixException(Exception):
    pass


class NoSuchPrefixException(Exception):
    pass


class Config():
    def __init__(self, group_id: int):
        self.__gid = group_id
        self.__default: str = ""
        self.__default_global: str = ""
        self.__wikis: dict = {}
        self.__wikis_global: dict = {}

        self.__parse_data(self.__get_config())
        self.__parse_global_data(self.__get_global_config())

    def add_wiki(self, prefix: str, api_url: str, url: str) -> bool:
        self.__wikis[prefix] = [api_url, url]
        if self.__default == "":
            self.__default = prefix

        return self.save_data()

    def add_wiki_global(self, prefix: str, api_url: str, url: str) -> bool:
        self.__wikis_global[prefix] = [api_url, url]
        if self.__default_global == "":
            self.__default_global = prefix

        return self.save_global_data()

    def del_wiki(self, prefix: str) -> bool:
        return self.__wikis.pop(prefix, "") != "" and self.save_data()

    def del_wiki_global(self, prefix: str) -> bool:
        return self.__wikis_global.pop(prefix, "") != "" and self.save_global_data()

    def __get_config(self) -> dict:
        file_name = f'{self.__gid}.json'
        path = WIKI_DIR / file_name
        if not WIKI_DIR.is_dir():
            os.makedirs(WIKI_DIR)
        if not path.is_file():
            with open(path, "w", encoding="utf-8") as w:
                w.write(json.dumps({}))

        data = json.loads(path.read_bytes())
        return data

    def __get_global_config(self) -> dict:
        file_name = 'global.json'
        path = WIKI_DIR / file_name
        if not WIKI_DIR.is_dir():
            os.makedirs(WIKI_DIR)
        if not path.is_file():
            with open(path, "w", encoding="utf-8") as w:
                w.write(json.dumps({}))

        data = json.loads(path.read_bytes())
        return data

    def __parse_data(self, data: dict):
        self.__default = data.get("default", "")
        self.__wikis = data.get("wikis", {})

    def __parse_global_data(self, data: dict):
        self.__default_global = data.get("default", "")
        self.__wikis_global = data.get("wikis", {})

    def get_from_prefix(self, prefix: str) -> tuple:
        temp_data: list = self.__wikis.get(prefix, [])
        temp_global_data: list = self.__wikis_global.get(prefix, [])
        if temp_data == [] and temp_global_data == []:  # 未获取到指定前缀时
            if self.__default == "" and self.__default_global == "":  # 没有配置默认前缀
                raise NoDefaultPrefixException
            elif self.__default != "":  # 本群设置了默认前缀
                temp_data: list = self.__wikis.get(self.__default, [])
                if temp_data == []:  # 没有从本群的列表中找到对应wiki,回落到全局
                    temp_global_data = self.__wikis_global.get(self.__default, [])
                    if temp_global_data == []:
                        raise NoSuchPrefixException
                    return temp_global_data[0], temp_global_data[1]
                else:
                    return temp_data[0], temp_data[1]
            else:  # 有全局默认前缀（此时强制使用全局数据库）
                temp_global_data: list = self.__wikis_global.get(self.__default_global, [])
                if temp_global_data == []:
                    raise NoSuchPrefixException
                return temp_global_data[0], temp_global_data[1]
        elif temp_data == [] and temp_global_data != []:
            return temp_global_data[0], temp_global_data[1]
        else:
            return temp_data[0], temp_data[1]

    def save_data(self) -> bool:
        file_name = f"{self.__gid}.json"
        path = WIKI_DIR / file_name
        if not path.is_file():
            with open(path, "w", encoding="utf-8") as w:
                w.write(json.dumps({}))

        with open(path, "w", encoding="utf-8") as w:
            data: dict = {"default": self.__default, "wikis": self.__wikis}
            w.write(json.dumps(data, indent=4))

        return True

    def save_global_data(self) -> bool:
        file_name = f"global.json"
        path = WIKI_DIR / file_name
        if not path.is_file():
            with open(path, "w", encoding="utf-8") as w:
                w.write(json.dumps({}))

        with open(path, "w", encoding="utf-8") as w:
            data: dict = {"default": self.__default_global, "wikis": self.__wikis_global}
            w.write(json.dumps(data, indent=4))

        return True

    def set_default(self, default: str) -> bool:
        if default in self.__wikis:
            self.__default = default
            self.save_data()
            return True
        else:
            return False

    def set_default_global(self, default: str) -> bool:
        if default in self.__wikis_global:
            self.__default_global = default
            self.save_global_data()
            return True
        else:
            return False

    @property
    def list_data(self) -> tuple:
        count: int = 0
        temp_list: str = ""
        temp_list += f"本群默认：{self.__default}\n"
        temp_list += f"本群所有wiki：\n"
        for prefix in self.__wikis:
            count += 1
            temp_str: str = f"{count}前缀：{prefix}\n" + \
                            f"API地址：{self.__wikis.get(prefix)[0]}\n" + \
                            f"通用链接：{self.__wikis.get(prefix)[1]}\n"
            temp_list += temp_str

        count = 0
        temp_list_global: str = ""
        temp_list_global += f"全局默认：{self.__default_global}\n"
        temp_list_global += f"所有全局wiki：\n"
        for prefix in self.__wikis_global:
            count += 1
            temp_str: str = f"{count}前缀：{prefix}\n" + \
                            f"API地址：{self.__wikis_global.get(prefix)[0]}\n" + \
                            f"通用链接：{self.__wikis_global.get(prefix)[1]}\n"
            temp_list_global += temp_str

        return temp_list, temp_list_global