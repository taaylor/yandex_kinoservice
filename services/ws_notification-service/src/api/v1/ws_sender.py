from aiohttp import web
from storage.cache import Cache

routes = web.RouteTableDef()


@routes.get("/test")
async def index(request: web.Request) -> web.Response:
    cache: Cache = request.app.get("cache")
    await cache.set("key", "привет!", expire=10)
    return web.Response(text=(await cache.get("key")))
