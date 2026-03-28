import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging
import signal
import sys

from aiohttp import web
# import aiohttp_cors

import domio.config as config
from domio.bmp280 import init as bmp280_init
from domio.bmp280 import close as bmp280_close
from domio.bmp280 import get_pressure as get_pressure_data
from domio.bmp280 import get_sea_level_pressure as get_sea_level_pressure_data
from domio.bmp280 import get_temperature as get_temperature_data
from domio.canio import get_humidity as get_humidity_can
from domio.canio import get_temperature as get_temperature_can
from domio.canio import init as can_init
from domio.canio import close as can_close
from domio.gpio import close as gpio_close
from domio.gpio import init as gpio_init
import domio.i2c as i2c
from domio.linky import get_data as get_linky_data
from domio.linky import close as linky_close
from domio.linky import init as linky_init
from domio.logger import close as logger_close
from domio.logger import init as logger_init

logger = logging.getLogger(__name__)


async def outdoor_handler(request):
    data = {
        "humidity": get_humidity_can(),
        "temperature": get_temperature_can(),
    }
    return web.json_response({"data": data})


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


async def init():
    global _thread_executor

    _thread_executor = ThreadPoolExecutor(max_workers=3)

    bus = i2c.open_bus(config.i2c.bus)

    logger_init(config.loggers)
    can_init()
    bmp280_init(bus, config.general.altitude)
    await gpio_init()
    linky_init(_thread_executor)


async def close():
    global _thread_executor

    await bmp280_close()
    await can_close()
    await linky_close()
    await gpio_close()
    logger_close()

    i2c.close_bus()

    if _thread_executor is not None:
        _thread_executor.shutdown()
        _thread_executor = None


def make_app() -> web.Application:
    # run a server
    app = web.Application()

    app.router.add_get("/linky", linky_handler)
    app.router.add_get("/outdoor", outdoor_handler)
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

    await init()

    app = make_app()

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", config.general.port)
    logger.info("web server is running")
    await site.start()
    # await running

    while True:
        await asyncio.sleep(1)


def sigterm_handler(_signo, _stack_frame):
    # raises SystemExit(0):
    sys.exit(0)


def main():
    signal.signal(signal.SIGTERM, sigterm_handler)

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
