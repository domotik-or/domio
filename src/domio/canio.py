import asyncio
from functools import partial
import logging

import can
# from can.notifier import MessageRecipient

import domio.config as config
from domio.utils import done_callback
from domio.utils import exec_cmd

_running = True
_task = None

_humidity = 0.0
_temperature = 0.0

_bus = None
_notifier = None
_reader = None

# logger initial setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def handle_exception(loop, context):
    logger.debug(f"exception reason: {context['message']}")


def init():
    global _bus
    global _notifier
    global _reader
    global _task

    try:
        _bus = can.Bus(interface="socketcan", channel="can0")
    except can.exceptions.CanOperationError as exc:
        logger.error(f"something when wrong when connecting to can socket: {exc}")
        return

    _reader = can.AsyncBufferedReader()

    listeners = [_reader]
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(handle_exception)
    _notifier = can.Notifier(_bus, listeners, loop=loop)

    if _task is None:
        _task = asyncio.create_task(_can_task())
        _task.add_done_callback(partial(done_callback, logger))


async def _can_task():
    global _humidity
    global _temperature

    logger.info("started")

    counter = 0
    while _running:
        try:
            msg = await asyncio.wait_for(_reader.get_message(), 1)
        except asyncio.TimeoutError:
            counter += 1
            if counter == 30:
                counter = 0
                await exec_cmd("sudo systemctl restart can0-socket.service")
                logger.info("can interface restarted")
            continue

        # print(f"{msg.arbitration_id:X}: {msg.data}")
        _humidity = int.from_bytes(msg.data[2:4], byteorder="big", signed=True) / 100.0
        _temperature = int.from_bytes(msg.data[0:2], byteorder="big", signed=True) / 100.0

    logger.info("stopped")


def get_humidity() -> float:
    return _humidity


def get_temperature() -> float:
    return _temperature


async def close():
    global _running
    global _task

    _notifier.stop()

    _running = False
    if _task is not None:
        try:
            await _task
        except Exception:
            # task exceptions are handled by the done callback
            pass
        _task = None

    _bus.shutdown()


async def run(config_filename: str):
    config.read(config_filename)

    init()

    for _ in range(20):
        humidity = get_humidity()
        temperature = get_temperature()
        logger.debug(f"temperature: {temperature}°C, humidity: {humidity} Pa")

        await asyncio.sleep(1)


# main is used for test purpose as standalone
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
