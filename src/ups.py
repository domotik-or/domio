#!/usr/bin/env python3

import asyncio
from datetime import datetime
from datetime import timedelta
import logging

import pigpio
from aiomqtt import Client

import config


_ac220 = False
_last_on = datetime.now()
_pi = None
_running = True
_task = None

logger = logging.getLogger(__name__)


async def init():
    global _task
    global _pi

    if _pi is None:
        _pi = pigpio.pi()

    _pi.set_mode(config.ups.ac220_gpio, pigpio.INPUT)
    _pi.set_pull_up_down(config.ups.ac220_gpio, pigpio.PUD_OFF)

    _pi.set_mode(config.ups.buzzer_gpio, pigpio.OUTPUT)

    _task = asyncio.create_task(_task_ups())


async def _publish(state: bool):
    payload = "1" if state else "0"
    async with Client(config.mqtt.host, config.mqtt.port) as client:
        await client.publish("home/mains/presence", payload=payload)


async def _task_ups():
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

    _running = False
    await _task


def get_220v_status():
    return _ac220


# main is used for test purpose as standalone
async def run(config_filename: str):
    global _running

    config.read(config_filename)

    await init()

    for _ in range(50):
        data = get_220v_status()
        print(data)
        await asyncio.sleep(1)

    await close()


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

    try:
        asyncio.run(run(args.config))
    except KeyboardInterrupt:
        pass

    logger.info("application stopped")
