import smbus2

_bus = None


def open_bus(bus_num: int):
    global _bus
    _bus = smbus2.SMBus(bus_num)


def close_bus():
    if _bus is not None:
        _bus.close()


def get_bus() -> smbus2.SMBus:
    return _bus
