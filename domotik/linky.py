#!/usr/bin/env python3

import asyncio
import logging

import serial
import serial_asyncio

import domotik.config as config


_reader = None
_running = True
_task = None

_east = 0
_easf01 = 0
_easf02 = 0
_smaxsn = 0
_sinsts = 0
_smaxsn = 0
_smaxsn_1 = 0

logger = logging.getLogger(__name__)


async def init():
    global _reader
    global _task

    _reader, _ = await serial_asyncio.open_serial_connection(
        url=config.linky.serial_port,
        baudrate=config.linky.baudrate,
        bytesize=get_data(serial, config.linky.bytesize),
        parity=get_data(serial, config.linky.parity),
        stopbits=get_data(serial, config.linky.stopbits)
    )

    _task = asyncio.create_task(_task_linky())


async def _task_linky():
    global _east
    global _easf01
    global _easf02
    global _smaxsn
    global _sinsts
    global _smaxsn
    global _smaxsn_1

    try:
        while _running:
            line_bytes = (await _reader.readline()).strip()

            try:
                line = line_bytes.decode()
            except UnicodeDecodeError:
                continue
            parts = line.split('\t')

            if len(parts) >= 2:
                checksum = parts[-1]
                ok = chr((sum(line_bytes[:-1]) & 0x3f) + 0x20) == checksum
                if ok and parts[0] in [
                    "EAST", "EASF01", "EASF02", "SINSTS", "SMAXSN", "SMAXSN-1"
                ]:
                    # print(parts)
                    if parts[0] == "EAST":
                        _east = int(parts[1], 10)
                    elif parts[0] == "EASF01":
                        _easf01 = int(parts[1], 10)
                    elif parts[0] == "EASF02":
                        _easf02 = int(parts[1], 10)
                    elif parts[0] == "SINSTS":
                        _sinsts = int(parts[1], 10)
                    elif parts[0] == "SMAXSN":
                        _smaxsn = int(parts[2], 10)
                    elif parts[0] == "SMAXSN-1":
                        _smaxsn_1 = int(parts[2], 10)
    except KeyboardInterrupt:
        return


async def close():
    global _running

    _running = False
    await _task


def get_data():
    return {
        "east": _east,
        "easf01": _easf01,
        "easf02": _easf02,
        "smaxsn": _smaxsn,
        "sinsts": _sinsts,
        "smaxsn": _smaxsn,
        "smaxsn_1": _smaxsn_1
    }


# main is used for test purpose as standalone
async def main():
    global _running

    await init()

    for _ in range(20):
        data = get_data()
        print(data)
        await asyncio.sleep(3)

    _running = False
    await _task


if __name__ == "__main__":
    import sys

    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter("%(asctime)s %(module)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
