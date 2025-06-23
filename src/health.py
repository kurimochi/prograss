import asyncio
from aiohttp import web
from logger import get_logger

logger = get_logger(__name__)


async def handle(_):
    try:
        logger.info("Received health check request.")
        return web.Response(text="OK")
    except Exception as e:
        logger.exception(f"Error in health check handler: {e}")
        return web.Response(status=500, text="Internal Server Error")


async def start_health_server():
    try:
        app = web.Application()
        app.router.add_get("/", handle)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 8080)
        await site.start()
        logger.info("Health check server started on port 8080.")
    except Exception as e:
        logger.exception(f"Failed to start health server: {e}")
        raise


if __name__ == "__main__":

    async def main():
        try:
            await start_health_server()
            logger.info("Entering infinite wait loop to keep server alive.")
            await asyncio.Event().wait()
        except Exception as e:
            logger.exception(f"Health server crashed: {e}")

    asyncio.run(main())
