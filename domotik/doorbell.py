#!/usr/bin/env python3

import argparse
import asyncio
import importlib
import logging

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
        pigpio.EITHER_EDGE,
        __callback
    )

    asyncio.create_task(__subscribe())


async def __publish(state: bool):
    payload = "pressed" if state else "released"
    async with Client(config.mqtt.host, config.mqtt.port) as client:
        await client.publish("home/doorbell/button", payload=payload)


def __callback(gpio: int, level: int, tick: int):
    if level == 1:
        logger.info("door bell button pressed")
    _loop.create_task(__publish(level==1))


async def __ring():
    global _task

    try:
        for s in range(5):
            _pi.write(config.doorbell.bell_gpio, True)
            logger.debug("ding")
            await asyncio.sleep(0.8)

            _pi.write(config.doorbell.bell_gpio, False)
            logger.debug("dong")
            await asyncio.sleep(1.2)
            if not _running:
                return
    finally:
        _pi.write(config.doorbell.bell_gpio, False)
        _task = None


async def __subscribe():
    global _task

    async with Client(config.mqtt.host, config.mqtt.port) as client:
        await client.subscribe("home/doorbell/bell")
        async for message in client.messages:
            if _task is None:
                logger.info("ring the bell")
                # the task is run using the loop of the main thread
                # enabling _task to be tested without using a critical section
                _task = _loop.create_task(__ring())


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

    await asyncio.sleep(20)

    await close()


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

    try:
        asyncio.run(run(args.config))
    except KeyboardInterrupt:
        pass

    logger.info("application stopped")
