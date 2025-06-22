import discord
import os
import cron
from discord import app_commands
from db import init_db
from commands import register, unregister, submit, aggregate, config, showconf, fubuki

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

conn, cursor = init_db()


@client.event
async def on_ready():
    cron.start()
    await tree.sync()
    print("READY")


register.setup(tree, conn, cursor, client)
unregister.setup(tree, conn, cursor)
submit.setup(tree, conn, cursor)
aggregate.setup(tree, cursor)
config.setup(tree, conn, cursor, client)
showconf.setup(tree, conn, cursor, client)
fubuki.setup(tree)
cron = cron.setup_cron(conn, cursor, client)

client.run(TOKEN)
