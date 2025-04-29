#!/usr/bin/env python3

import asyncio
from datetime import datetime
from datetime import timedelta
from functools import partial
import logging

import pigpio
from aiomqtt import Client

import domio.config as config
from domio.utils import done_callback

_ac220 = False
_last_on = datetime.now()
_pi = None
_running = True
_task = None

# logger initial setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def init():
    global _task
    global _pi

    if _pi is None:
        _pi = pigpio.pi()

    _pi.set_mode(config.ups.ac220_gpio, pigpio.INPUT)
    _pi.set_pull_up_down(config.ups.ac220_gpio, pigpio.PUD_OFF)

    _pi.set_mode(config.ups.buzzer_gpio, pigpio.OUTPUT)

    if _task is None:
        _task = asyncio.create_task(_ups_task())
        _task.add_done_callback(partial(done_callback, logger))


async def _publish(state: bool):
    payload = "1" if state else "0"
    async with Client(config.mqtt.hostname, config.mqtt.port) as client:
        await client.publish("home/mains/presence", payload=payload)


async def _ups_task():
    global _ac220
    global _last_on

    ac220_old = True

    try:
        while _running:
            _ac220 = not _pi.read(config.ups.ac220_gpio)

            if _ac220 != ac220_old:
                if _ac220:
                    _pi.write(config.ups.buzzer_gpio, False)
                    logger.info("220V power supply is on")
                    await _publish(True)
                else:
                    _pi.write(config.ups.buzzer_gpio, True)
                    logger.info("220V power supply is off")
                    await _publish(False)

            ac220_old = _ac220

            if _ac220:
                _last_on = datetime.now()
            else:
                if datetime.now() - _last_on > timedelta(minutes=5):
                    # shutdown after 5 minutes after lacking 220 V power
                    logger.debug("shutdown requested")
                    await asyncio.create_subprocess_shell(
                        "sudo shutdown -h now",
                        shell=True,
                        stdout=asyncio.subprocess.DEVNULL,
                        stderr=asyncio.subprocess.DEVNULL
                    )

            await asyncio.sleep(1)

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


def get_220v_status():
    return _ac220


# main is used for test purpose as standalone
async def run(config_filename: str):
    global _running

    config.read(config_filename)

    await init()

    for _ in range(50):
        data = get_220v_status()
        logger.debug(data)
        await asyncio.sleep(1)


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

    logger.info("application stopped")

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
