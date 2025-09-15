

import time
from os import path, listdir


class Pointer:
    def __init__(self, path_to_folder, log):
        self.__log = log
        self.__directory = path.dirname(path_to_folder)

    def sort_db_files(self):
        all_files = listdir(self.__directory)
        all_db_files = sorted(filter(lambda file: file.endswith(".db"), all_files))
        return all_db_files

    @staticmethod
    def generate_new_file_name():
        prefix = "data_"
        ts = str(int(time.time()) * 1000)
        db_file_name = f"{prefix}{ts}.db"
        return db_file_name
