import asyncio

from aiohttp import web

from tic import close
from tic import get_data
from tic import init


async def index_handler(request):
    data = get_data()
    return web.json_response(data)


async def startup(app):
    await init()


async def cleanup(app):
    await close()


def main():
    app = web.Application()
    app.router.add_get("/", index_handler)
    app.on_startup.append(startup)
    app.on_cleanup.append(cleanup)
    web.run_app(app)


if __name__ == "__main__":
    main()
