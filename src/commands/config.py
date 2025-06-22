import discord
import re
from discord import app_commands
from db import registered
from views import gen_error_embed
from utils import channel_judge


def setup(tree, conn, cursor, client):
    @tree.command(name="config", description="設定を変更")
    @app_commands.describe(
        key="変更する項目",
        value="変更後の値 (channel -> チャンネルをメンション  notice -> HH:MM)",
    )
    @app_commands.choices(
        key=[
            app_commands.Choice(name="channel", value="channel"),
            app_commands.Choice(name="notice", value="notice"),
        ]
    )
    async def config(ctx: discord.Interaction, key: str, value: str):
        user_id = ctx.user.id
        if not registered(user_id, cursor):
            embed = gen_error_embed(
                "You are not yet registered.", "Please register using /register."
            )
            await ctx.response.send_message(embed=embed, ephemeral=True)
            return

        if key == "channel":
            channel = channel_judge(value, client)
            if channel:
                cursor.execute(
                    "SELECT 1 FROM channels WHERE user_id = %s AND channel = %s LIMIT 1",
                    (
                        user_id,
                        channel,
                    ),
                )
                if cursor.fetchone() is None:
                    cursor.execute(
                        "INSERT INTO channels (user_id, channel) VALUES (%s, %s)",
                        (
                            user_id,
                            channel,
                        ),
                    )
                    conn.commit()
                    embed = discord.Embed(
                        title="Channel config have been successfully updated",
                        color=0x219DDD,
                    )
                else:
                    cursor.execute(
                        "SELECT 1 FROM channels WHERE user_id = %s AND channel != %s LIMIT 1",
                        (
                            user_id,
                            channel,
                        ),
                    )
                    if cursor.fetchone():
                        cursor.execute(
                            "DELETE FROM channels WHERE user_id = %s AND channel = %s",
                            (
                                user_id,
                                channel,
                            ),
                        )
                        conn.commit()
                        embed = discord.Embed(
                            title="Channel config have been successfully updated",
                            color=0x219DDD,
                        )
                    else:
                        embed = gen_error_embed(
                            "Too few channels set.", "Add 1 or more channels."
                        )
            else:
                embed = gen_error_embed(
                    "Invalid channel parameter.",
                    "Please mention the channels that exist.",
                )
        elif key == "notice":
            # H:MMまたはHH:MMを許容
            if re.fullmatch(r"[0-9]:[0-5][0-9]", value):
                value = f"0{value}"
            elif not re.fullmatch(r"([01][0-9]|2[0-3]):[0-5][0-9]", value):
                value = ""
            cursor.execute(
                "UPDATE users SET notice = %s WHERE user_id = %s",
                (
                    value,
                    user_id,
                ),
            )
            conn.commit()
            embed = discord.Embed(
                title="Notice config have been successfully updated", color=0x219DDD
            )
            embed.add_field(
                name="New config:", value="No notice" if value == "" else value
            )
        else:
            embed = gen_error_embed(
                "A key that does not exist.", "Please specify a key that exists."
            )
        await ctx.response.send_message(embed=embed, ephemeral=True)
