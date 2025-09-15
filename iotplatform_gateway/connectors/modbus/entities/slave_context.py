

from pymodbus.datastore.context import ModbusSlaveContext
from pymodbus.datastore.store import ModbusSequentialDataBlock


class SlaveContext(ModbusSlaveContext):
    """
    Monkey-patched version of ModbusSlaveContext to allow initialization
    with custom data blocks for each type of data.
    Can be removed when the issue with ModbusSlaveContext is fixed in pymodbus.
    """

    def __init__(self, *_args, di=None, co=None, ir=None, hr=None):
        self.store = {}
        self.store["d"] = di if di is not None else ModbusSequentialDataBlock.create()
        self.store["c"] = co if co is not None else ModbusSequentialDataBlock.create()
        self.store["i"] = ir if ir is not None else ModbusSequentialDataBlock.create()
        self.store["h"] = hr if hr is not None else ModbusSequentialDataBlock.create()
