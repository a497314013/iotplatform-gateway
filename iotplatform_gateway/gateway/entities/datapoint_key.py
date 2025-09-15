# ------------------------------------------------------------------------------

#
# ------------------------------------------------------------------------------

from iotplatform_gateway.gateway.entities.report_strategy_config import ReportStrategyConfig


class DatapointKey:
    def __init__(self, key, report_strategy: ReportStrategyConfig = None):
        self.key = key
        self.report_strategy = report_strategy

    def __str__(self):
        return f"DatapointKey(key={self.key}, report_strategy={self.report_strategy})"

    def __repr__(self):
        return self.__str__()

    def __hash__(self):
        return hash((self.key, self.report_strategy))

    def __eq__(self, other):
        if isinstance(other, DatapointKey):
            return self.key == other.key and self.report_strategy == other.report_strategy
        return False
