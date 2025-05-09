#!/usr/bin/env python3

import asyncio
from functools import partial
import logging

import serial
import serial_asyncio

import domio.config as config
from domio.utils import done_callback

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

# logger initial setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def init():
    global _reader
    global _task

    _reader, _ = await serial_asyncio.open_serial_connection(
        url=config.linky.serial_port,
        baudrate=config.linky.baudrate,
        bytesize=getattr(serial, config.linky.bytesize),
        parity=getattr(serial, config.linky.parity),
        stopbits=getattr(serial, config.linky.stopbits)
    )

    if _task is None:
        _task = asyncio.create_task(_task_linky())
        _task.add_done_callback(partial(done_callback, logger))


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
                crc_ok = chr((sum(line_bytes[:-1]) & 0x3f) + 0x20) == checksum
                if crc_ok:
                    logger.debug(parts[0])

                    if parts[0] in [
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
                        else:
                            continue
                else:
                    logger.debug("invalid checksum")

    except KeyboardInterrupt:
        return


async def close():
    global _running
    global _task

    _running = False

    if _task is not None:
        try:
            await _task
        except Exception:
            # task exceptions are handled by the done callback
            pass
        _task = None


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
async def run(config_filename: str):
    global _running

    config.read(config_filename)

    await init()

    for _ in range(20):
        data = get_data()
        logger.debug(data)
        await asyncio.sleep(3)


if __name__ == "__main__":
    import argparse
    import sys

    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter("%(asctime)s %(module)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="config.toml")
    args = parser.parse_args()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run(args.config))
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(close())
        loop.stop()
        logger.info("done")
