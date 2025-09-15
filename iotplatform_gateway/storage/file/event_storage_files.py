

from threading import RLock
from typing import Dict


class EventStorageFiles:
    def __init__(self, state_file, data_files: Dict[str, bool]):
        self.state_file = state_file
        self.data_files = data_files
        self.__data_files_lock = RLock()

    def get_state_file(self):
        return self.state_file

    def get_data_files(self):
        with self.__data_files_lock:
            return sorted(self.data_files.keys())

    def add_data_file(self, data_file):
        with self.__data_files_lock:
            self.data_files[data_file] = False

    def remove_data_file(self, data_file):
        with self.__data_files_lock:
            del self.data_files[data_file]

    def confirm_file_processed(self, data_file):
        with self.__data_files_lock:
            self.data_files[data_file] = True
