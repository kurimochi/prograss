import discord
import os
import cron
from discord import app_commands
from logging import getLogger, StreamHandler, Formatter, INFO
from db import init_db
from commands import register, unregister, submit, aggregate, config, showconf, fubuki

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(INFO)
formatter = Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
handler.setFormatter(formatter)
logger.setLevel(INFO)
logger.addHandler(handler)
logger.propagate = False

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

conn, cursor = init_db()
logger.info("DB initialized.")


@client.event
async def on_ready():
    global cron_instance
    try:
        if cron_instance is None:
            cron_instance = await cron.setup_cron(conn, cursor, client)
        cron_instance.start()
        await tree.sync()
        logger.info("Bot is ready and commands synced.")
    except Exception as e:
        logger.exception(f"Failed to sync commands or start cron: {e}")
        exit(1)


try:
    register.setup(tree, conn, cursor, client)
    unregister.setup(tree, conn, cursor)
    submit.setup(tree, conn, cursor)
    aggregate.setup(tree, cursor)
    config.setup(tree, conn, cursor, client)
    showconf.setup(tree, conn, cursor, client)
    fubuki.setup(tree)
    cron_instance = None
except Exception as e:
    logger.exception(f"Failed to setup commands: {e}")
    exit(1)


@client.event
async def on_disconnect():
    if "cron_instance" in globals():
        cron_instance.stop()
        logger.info("Cron stopped.")


@client.event
async def on_shutdown():
    if conn:
        cursor.close()
        conn.close()
        logger.info("DB connection closed.")


if __name__ == "__main__":
    if not TOKEN:
        print("Error: DISCORD_TOKEN environment variable is not set.")
        exit(1)

    client.run(TOKEN)
