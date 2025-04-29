import argparse
import asyncio
import importlib
import logging
import sys

from aiohttp import web
# import aiohttp_cors

import domio.config as config
from domio.bmp280 import init as init_bmp280
from domio.bmp280 import close as close_bmp280
from domio.bmp280 import get_pressure as get_pressure_data
from domio.bmp280 import get_sea_level_pressure as get_sea_level_pressure_data
from domio.bmp280 import get_temperature as get_temperature_data
from domio.doorbell import close as close_doorbell
from domio.doorbell import init as init_doorbell
import domio.i2c as i2c
from domio.linky import close as close_linky
from domio.linky import get_data as get_linky_data
from domio.linky import init as init_linky
from domio.ups import init as init_ups

__version__ = "1.0.0"

logger = logging.getLogger()
handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter("%(asctime)s %(module)s %(levelname)s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


async def linky_handler(request):
    data = get_linky_data()
    return web.json_response({"data": data})


async def pressure_handler(request):
    value = get_pressure_data()
    return web.json_response({"data": {"pressure": value}})


async def pressure_at_sea_level_handler(request):
    value = get_sea_level_pressure_data()
    return web.json_response({"data": {"sea-level-pressure": value}})


async def temperature_handler(request):
    value = get_temperature_data()
    return web.json_response({"data": {"temperature": value}})


def _set_loggers_level(config_loggers: dict, module_path: list):
    # set log level of modules logger
    for lg_name, lg_config in config_loggers.items():
        if isinstance(lg_config, dict):
            module_path.append(lg_name)
            _set_loggers_level(lg_config, module_path)
        elif isinstance(lg_config, str):
            this_module_path = '.'.join(module_path + [lg_name])
            try:
                importlib.import_module(this_module_path)
            except ModuleNotFoundError:
                logger.warning(f"module {this_module_path} not found")
                continue

            level = getattr(logging, lg_config)
            if this_module_path in logging.Logger.manager.loggerDict.keys():
                logging.getLogger(this_module_path).setLevel(level)
        else:
            raise Exception("incorrect type")


async def startup(app):
    _set_loggers_level(config.loggers, [])

    bus = i2c.open_bus(config.i2c.bus)

    init_bmp280(bus, config.general.altitude)
    await init_doorbell()
    await init_linky()
    await init_ups()


async def cleanup(app):
    await close_bmp280()
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

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", config.network.server_port)
    await site.start()
    while True:
        await asyncio.sleep(1)


async def close():
    pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="config.toml")
    args = parser.parse_args()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        logger.info("server started")
        loop.run_until_complete(run(args.config))
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(close())
        loop.stop()
        logger.info("server stopped")
