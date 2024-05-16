#!/usr/bin/env python3

import argparse
import asyncio
import importlib
import logging
import sys

from aiohttp import web
# import aiohttp_cors

from domotik.bmp180 import init as init_bmp180
from domotik.bmp180 import close as close_bmp180
from domotik.bmp180 import get_pressure as get_pressure_data
from domotik.bmp180 import get_sea_level_pressure as get_sea_level_pressure_data
from domotik.bmp180 import get_temperature as get_temperature_data
import domotik.config as config
from domotik.doorbell import close as close_doorbell
from domotik.doorbell import init as init_doorbell
import domotik.i2c as i2c
from domotik.linky import close as close_linky
from domotik.linky import get_data as get_linky_data
from domotik.linky import init as init_linky
from utils import get_project_root

logger = logging.getLogger()
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter("%(asctime)s %(module)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


async def linky_handler(request):
    data = get_linky_data()
    return web.json_response(data)


async def pressure_handler(request):
    data = get_pressure_data()
    return web.json_response(data)


async def pressure_at_sea_level_handler(request):
    data = get_sea_level_pressure_data()
    return web.json_response(data)


async def temperature_handler(request):
    data = get_temperature_data()
    return web.json_response(data)


# TODO: future use
# async def init():
async def startup(app):
    # set log level of modules' loggers
    for lg_name, lg_level in config.loggers.items():
        if lg_name == "root":
            logger.setLevel(lg_level)
        else:
            module = sys.modules[lg_name]
            module_logger = getattr(module, "logger")
            module_logger.setLevel(lg_level)

    i2c.open_bus(config.i2c.bus)

    init_bmp180(config.general.altitude)
    await init_doorbell()
    await init_linky()


# TODO: future use
# async def close():
async def cleanup(app):
    await close_bmp180()
    await close_doorbell()
    await close_linky()

    i2c.close_bus


async def make_app():
    # run a server
    app = web.Application()

    app.on_startup.append(startup)
    app.on_cleanup.append(cleanup)

    app.router.add_get("/linky", linky_handler)
    app.router.add_get("/pressure", pressure_handler)
    app.router.add_get("/pressure/sealevel", pressure_at_sea_level_handler)
    app.router.add_get("/temperature", temperature_handler)

    # cors = aiohttp_cors.setup(app, defaults={
    #     "*": aiohttp_cors.ResourceOptions(
    #         allow_credentials=True,
    #         expose_headers="*",
    #         allow_headers="*",
    #     )
    # })
    #
    # # Configure CORS on all routes.
    # for route in list(app.router.routes()):
    #     cors.add(route)

    return app


async def run(config_filename: str):
    config.read(config_filename)

    # await init()

    app = await make_app()
    app["config"] = config

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", config.linky.server_port)
    await site.start()
    while True:
        await asyncio.sleep(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="config.toml")
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    try:
        logger.info("server started")
        loop.run_until_complete(run(args.config))
    except KeyboardInterrupt:
        pass
    finally:
        # TODO: future use
        # loop.run_until_complete(close())
        loop.stop()
        logger.info("server stopped")
    pass


if __name__ == "__main__":
    main()
