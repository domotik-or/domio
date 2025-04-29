import asyncio

from smbus2 import SMBus

_bus = None
_lock = asyncio.Lock()


def open_bus(bus_num: int) -> SMBus:
    global _bus
    global _lock

    if _bus is None:
        _bus = SMBus(bus_num)

    return _bus


def close_bus():
    global _bus

    if _bus is not None:
        _bus.close()
        _bus = None


async def lock():
    global _lock

    await _lock.acquire()


def unlock():
    global _lock

    _lock.release()
