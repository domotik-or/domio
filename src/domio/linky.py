#!/usr/bin/env python3

import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import time

import serial

import domio.config as config

_serial = None
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


def init(executor: ThreadPoolExecutor):
    global _task
    global _serial

    try:
        _serial = serial.Serial(
            port=config.linky.serial_port,
            baudrate=config.linky.baudrate,
            timeout=0.5,
            bytesize=getattr(serial, config.linky.bytesize),
            parity=getattr(serial, config.linky.parity),
            stopbits=getattr(serial, config.linky.stopbits)
        )
    except serial.serialutil.SerialException:
        logger.error("cannot initialize airmar serial port")
    except Exception as exc:
        logger.error(f"unknown exception {exc}")
    else:
        if _task is None:
            _task = asyncio.create_task(_run_task(executor))


async def _run_task(executor: ThreadPoolExecutor):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, _linky_thread)


def _reset_input_buffer():
    while True:
        try:
            n = _serial.in_waiting
            if n == 0:
                return
            _serial.read(n)
        except serial.serialutil.SerialException:
            continue


def _linky_thread():
    global _east
    global _easf01
    global _easf02
    global _smaxsn
    global _sinsts
    global _smaxsn
    global _smaxsn_1

    logger.info("started")

    _serial.reset_input_buffer()
    logger.debug("ready")

    data = ""
    line = ""
    while _running:
        try:
            d = _serial.read(100)
        except serial.serialutil.SerialException:
            time.sleep(0.1)
            continue

        if len(d) == 0:
            # timeout
            continue

        try:
            data += d.decode()
        except UnicodeDecodeError:
            continue

        while True:
            if data[-1] in "\r\x03\x02\n":
                break

            index1 = data.find("\r\n")
            index2 = data.find("\r\x03\x02\n")

            if index1 == -1:
                # sometimes the end of line is \r\x03\x02\n not \r\n
                if index2 == -1:
                    break
                else:
                    line += data[:index2]
                    data = data[index2 + 4:]
            else:
                if index2 == -1:
                    line += data[:index1]
                    data = data[index1 + 2:]
                else:
                    if index1 < index2:
                        line += data[:index1]
                        data = data[index1 + 2:]
                    else:
                        line += data[:index2]
                        data = data[index2 + 4:]

            line = line.strip()
            parts = line.split('\t')

            if len(parts) >= 2:
                checksum = parts[-1]
                crc_ok = chr((sum(bytes(line[:-1], encoding="ascii")) & 0x3f) + 0x20) == checksum
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

            line = ""

    logger.info("stopped")


async def close():
    global _running
    global _task

    if _task is not None and _running:
        try:
            _running = False
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
    from concurrent.futures import ThreadPoolExecutor

    config.read(config_filename)

    thread_executor = ThreadPoolExecutor(max_workers=3)
    init(thread_executor)

    for _ in range(20):
        data = get_data()
        logger.debug(data)
        await asyncio.sleep(3)

    thread_executor.shutdown()


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
