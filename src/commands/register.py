import discord
from discord import app_commands
from db import registered
from views import gen_error_embed
from utils import channel_judge


def setup(tree, conn, cursor, client):
    @tree.command(name="register", description="prograssに登録")
    @app_commands.describe(
        channel="定期メッセージを送信するチャンネル (メンション or ID)"
    )
    async def register(ctx: discord.Interaction, channel: str):
        user_id = ctx.user.id
        if registered(user_id, cursor):
            embed = gen_error_embed(
                "You are already registered",
                "If you think this is a mistake, please contact the developer",
            )
        else:
            channel, judge = channel_judge(channel, client)
            if judge:
                cursor.execute("INSERT INTO users (user_id) VALUES (%s)", (user_id,))
                cursor.execute(
                    "INSERT INTO channels (user_id, channel) VALUES (%s, %s)",
                    (
                        user_id,
                        channel,
                    ),
                )
                conn.commit()
                embed = discord.Embed(title="Registration completed", color=0x219DDD)
            else:
                embed = gen_error_embed(
                    "Invalid channel parameter",
                    "Please mention the channels that exist",
                )
        await ctx.response.send_message(embed=embed)
