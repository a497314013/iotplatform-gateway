

from abc import ABC, abstractmethod


class EventStorage(ABC):

    def __init__(self, config, logger, main_stop_event):
        self._config = config
        self._main_stop_event = main_stop_event

    @abstractmethod
    def put(self, event):
        pass

    @abstractmethod
    def get_event_pack(self):
        # Returns events from pack
        pass

    @abstractmethod
    def event_pack_processing_done(self):
        # Indicates that events from previous "get_event_pack" may be cleared
        pass

    @abstractmethod
    def stop(self):
        # Stop the storage processing
        pass

    @abstractmethod
    def len(self):
        pass

    @abstractmethod
    def update_logger(self):
        pass

    def get_configuration(self):
        return self._config
