

from iotplatform_gateway.gateway.statistics.statistics_service import StatisticsService


class CollectStatistics:
    def __init__(self, start_stat_type, end_stat_type=None):
        self.start_stat_type = start_stat_type
        self.end_stat_type = end_stat_type

    def __call__(self, func):
        def inner(*args, **kwargs):
            try:
                _, __, data = args
                self.collect(self.start_stat_type, data)
            except ValueError:
                pass

            result = func(*args, **kwargs)
            if result and self.end_stat_type:
                self.collect(self.end_stat_type, result)

            return result

        return inner

    @staticmethod
    def collect(stat_type, data):
        bytes_count = str(data).__sizeof__()
        StatisticsService.add_bytes(stat_type, bytes_count)


class CollectAllReceivedBytesStatistics(CollectStatistics):
    def __call__(self, func):
        def inner(*args, **kwargs):
            try:
                _, data = args
                self.collect(self.start_stat_type, data)
            except ValueError:
                pass

            result = func(*args, **kwargs)
            return result

        return inner


class CollectAllSentTBBytesStatistics(CollectAllReceivedBytesStatistics):
    def __call__(self, func):
        return super().__call__(func)


class CollectRPCReplyStatistics(CollectStatistics):
    def __call__(self, func):
        def inner(*args, **kwargs):
            data = kwargs.get('content')
            if data:
                self.collect(self.start_stat_type, data)

            func(*args, **kwargs)

        return inner


class CollectStorageEventsStatistics(CollectStatistics):
    def __call__(self, func):
        def inner(*args, **kwargs):
            try:
                data = args[1]
                connector_name = args[2]
                if data:
                    StatisticsService.count_connector_message(connector_name, self.start_stat_type)
            except IndexError:
                pass

            func(*args, **kwargs)

        return inner


class CountMessage(CollectStatistics):
    def __call__(self, func):
        def inner(*args, **kwargs):
            StatisticsService.add_count(self.start_stat_type)
            result = func(*args, **kwargs)
            return result

        return inner
