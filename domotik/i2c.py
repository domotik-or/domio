import sm_bus2

_bus = None


def open_bus(_bus_num: int) -> sm_bus2.SMBus:
    global _bus
    _bus = sm_bus2.SMBus(_bus_num)
    return _bus


def close_bus():
    if _bus is not None:
        _bus.close()


def get_bus():
    return _bus
