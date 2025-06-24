import asyncio
from aiohttp import web
from cron import cron
from logger import get_logger

logger = get_logger(__name__)


async def health_handle(request):
    try:
        logger.info("Received health check request.")
        return web.Response(text="OK")
    except Exception as e:
        logger.exception(f"Error in health check handler: {e}")
        return web.Response(status=500, text="Internal Server Error")


async def cron_handle(request, conn, cursor, client):
    try:
        logger.debug("Received cron request.")
        await cron(conn, cursor, client)
        return web.Response(text="Cron job executed successfully")
    except Exception as e:
        logger.exception(f"Error in cron handler: {e}")
        return web.Response(status=500, text="Internal Server Error")


async def cron_error_handle(request):
    try:
        logger.warning("Unavailable cron called.")
        return web.Response(
            status=500, text="Cron not available, missing DB connection or client."
        )
    except Exception as e:
        logger.exception(f"Error in cron error handler: {e}")
        return web.Response(status=500, text="Internal Server Error")


async def start_web_server(conn=None, cursor=None, client=None):
    try:
        app = web.Application()
        app.router.add_get("/health", health_handle)
        if conn and cursor and client:
            app.router.add_get(
                "/cron", lambda request: cron_handle(request, conn, cursor, client)
            )
        else:
            app.router.add_get("/cron", cron_error_handle)
            logger.warning(
                "Cron endpoint not available due to missing DB connection or client."
            )
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", 8080)
        await site.start()
        logger.info("Web server started on port 8080.")
    except Exception as e:
        logger.exception(f"Failed to start web server: {e}")
        raise


if __name__ == "__main__":

    async def main():
        try:
            await start_web_server()
            logger.info("Entering infinite wait loop to keep server alive.")
            await asyncio.Event().wait()
        except Exception as e:
            logger.exception(f"Web server crashed: {e}")

    asyncio.run(main())
