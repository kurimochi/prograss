import discord
import re
from discord import app_commands
from db import registered
from views import gen_error_embed
from utils import channel_judge
from logger import get_logger

logger = get_logger(__name__)


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
        logger.info(f"User %s invoked /config key=%s value=%s", user_id, key, value)

        try:
            # 登録チェック
            if not registered(user_id, cursor):
                logger.warning(f"Unregistered user {user_id} tried /config")
                embed = gen_error_embed(
                    "You are not yet registered.", "Please register using /register."
                )
                await ctx.response.send_message(embed=embed, ephemeral=True)
                return

            # チャンネル設定
            if key == "channel":
                channel = channel_judge(value, client)
                if channel:
                    # チャンネル存在チェック
                    cursor.execute(
                        "SELECT 1 FROM channels WHERE user_id = %s AND channel = %s LIMIT 1",
                        (user_id, channel),
                    )
                    exists = cursor.fetchone() is not None

                    if not exists:
                        cursor.execute(
                            "INSERT INTO channels (user_id, channel) VALUES (%s, %s)",
                            (user_id, channel),
                        )
                        conn.commit()
                        logger.info("Channel %s added for user %s", channel, user_id)
                        embed = discord.Embed(
                            title="Channel config have been successfully updated",
                            color=0x219DDD,
                        )
                    else:
                        # 既存とは異なるチャンネルがあるか
                        cursor.execute(
                            "SELECT 1 FROM channels WHERE user_id = %s AND channel != %s LIMIT 1",
                            (user_id, channel),
                        )
                        other = cursor.fetchone() is not None
                        if other:
                            cursor.execute(
                                "DELETE FROM channels WHERE user_id = %s AND channel = %s",
                                (user_id, channel),
                            )
                            conn.commit()
                            logger.info(
                                "Channel %s removed for user %s", channel, user_id
                            )
                            embed = discord.Embed(
                                title="Channel config have been successfully updated",
                                color=0x219DDD,
                            )
                        else:
                            logger.warning(
                                "User %s tried to remove too few channels", user_id
                            )
                            embed = gen_error_embed(
                                "Too few channels set.", "Add 1 or more channels."
                            )
                else:
                    logger.error(
                        "Invalid channel parameter from user %s: %s", user_id, value
                    )
                    embed = gen_error_embed(
                        "Invalid channel parameter.",
                        "Please mention the channels that exist.",
                    )

            # 通知時間設定
            elif key == "notice":
                # H:MM または HH:MM を正規化
                if re.fullmatch(r"[0-9]:[0-5][0-9]", value):
                    value = f"0{value}"
                elif not re.fullmatch(r"([01][0-9]|2[0-3]):[0-5][0-9]", value):
                    logger.warning(
                        "Invalid notice format from user %s: %s", user_id, value
                    )
                    embed = gen_error_embed(
                        "Invalid time format.", "Please use HH:MM 24-hour format."
                    )
                    await ctx.response.send_message(embed=embed, ephemeral=True)
                    return

                cursor.execute(
                    "UPDATE users SET notice = %s WHERE user_id = %s",
                    (value, user_id),
                )
                conn.commit()
                logger.info("Notice time updated for user %s: %s", user_id, value)
                embed = discord.Embed(
                    title="Notice config have been successfully updated", color=0x219DDD
                )
                embed.add_field(
                    name="New config:", value="No notice" if value == "" else value
                )

            else:
                logger.error("Invalid config key from user %s: %s", user_id, key)
                embed = gen_error_embed(
                    "A key that does not exist.", "Please specify a key that exists."
                )

            await ctx.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            logger.exception("Exception in /config command for user %s", user_id)
            error_embed = gen_error_embed(
                "An unexpected error occurred.",
                "Please try again later or contact support.",
            )
            await ctx.response.send_message(embed=error_embed, ephemeral=True)
