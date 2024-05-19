#!/usr/bin/env python3

import argparse
import asyncio
import importlib
import logging
import time

import pigpio
from aiomqtt import Client

import domotik.config as config

_callback = None
_loop = None
_pi = None
_running = True
_task = None

logger = logging.getLogger(__name__)


async def init():
    global _callback
    global _loop
    global _pi

    if _pi is None:
        _pi = pigpio.pi()

    _pi.set_mode(config.doorbell.bell_gpio, pigpio.OUTPUT)
    _pi.set_mode(config.doorbell.button_gpio, pigpio.INPUT)
    _pi.set_glitch_filter(config.doorbell.button_gpio, 500)

    _loop = asyncio.get_event_loop()

    _callback = _pi.callback(
        config.doorbell.button_gpio,
        pigpio.RISING_EDGE,
        __callback
    )

    asyncio.create_task(__subscribe())


async def __publish():
    async with Client(config.mqtt.host, config.mqtt.port) as client:
        await client.publish("home/doorbell/timestamp", payload=f"{time.time()}")


def __callback(gpio: int, level: int, tick: int):
    if _task is None:
        # don't send notification if the bell is ringing
        logger.info("door bell button pressed")
        _loop.create_task(__publish())


async def __ding_dong():
    global _task

    try:
        for s in range(5):
            _pi.write(config.doorbell.bell_gpio, True)
            await asyncio.sleep(0.8)
            logger.debug("ding")

            _pi.write(config.doorbell.bell_gpio, False)
            await asyncio.sleep(1.2)
            logger.debug("dong")
            if not _running:
                return
    finally:
        _pi.write(config.doorbell.bell_gpio, False)
        _task = None


async def __subscribe():
    global _task

    async with Client(config.mqtt.host, config.mqtt.port) as client:
        await client.subscribe("home/doorbell/ring")
        async for message in client.messages:
            if _task is None:
                logger.info("ring the bell")
                # the task is run using the loop of the main thread
                # enabling _task to be tested without using a critical section
                _task = _loop.create_task(__ding_dong())


async def close():
    global _callback
    global _pi
    global _running

    logger.debug("closing")
    _running = False
    if _task is not None:
        await _task

    if _pi is not None:
        if _callback is not None:
            _callback.cancel()
            _callback = None

        _pi.stop()
        _pi = None


async def run(config_filename: str):
    config.read(config_filename)

    await init()

    await asyncio.sleep(1)

    __callback(0, 0, 0)

    while _running:
        await asyncio.sleep(1)
    else:
        logger.debug("loop end")


# main is used for test purpose as standalone
if __name__ == "__main__":
    import sys

    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter("%(asctime)s %(module)s %(levelname)s %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="config.toml")
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run(args.config))
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(close())
        loop.stop()
        logger.info("application stopped")
