#!/usr/bin/env python3

import argparse
import asyncio
import importlib
import logging
import sys

from aiohttp import web
# import aiohttp_cors

import domotik.config as config
from domotik.doorbell import close as close_doorbell
from domotik.doorbell import init as init_doorbell
from domotik.linky import close as close_linky
from domotik.linky import get_data
from domotik.linky import init as init_linky
from utils import get_project_root

logger = logging.getLogger()


async def index_handler(request):
    data = get_data()
    return web.json_response(data)


# TODO: future use
# async def init():
async def startup(app):
    # set log level of modules' loggers
    project_root = get_project_root()
    for lg_name, lg_config in config.loggers.items():
        module_name = f"{project_root}.{lg_name}"
        try:
            module = sys.modules[module_name]
        except KeyError:
            module = importlib.import_module(f"{project_root}.{lg_name}")
        module_logger = getattr(module, "logger")
        module_logger.setLevel(lg_config.level)

    await init_doorbell()
    await init_linky()


# TODO: future use
# async def close():
async def cleanup(app):
    await close_doorbell()
    await close_linky()


async def make_app():
    # run a server
    app = web.Application()

    app.on_startup.append(startup)
    app.on_cleanup.append(cleanup)

    app.router.add_get("/", index_handler)

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
