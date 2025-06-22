import discord
from discord import app_commands
from logger import get_logger
from db import registered
from views import gen_error_embed
from utils import channel_judge
import psycopg2

logger = get_logger(__name__)


def setup(tree, conn, cursor, client):
    @tree.command(name="register", description="prograssに登録")
    @app_commands.describe(
        channel="定期メッセージを送信するチャンネル (メンション or ID)"
    )
    async def register(ctx: discord.Interaction, channel: str):
        user_id = ctx.user.id
        logger.info(f"/register called by user {user_id}")

        embed = None

        try:
            if registered(user_id, cursor):
                embed = gen_error_embed(
                    "You are already registered.",
                    "If you think this is a mistake, please contact the developer.",
                )
                await ctx.response.send_message(embed=embed)
                logger.info(
                    f"Registration: User already registered - no action taken for user {user_id}"
                )
                return

            try:
                channel = channel_judge(channel, client)
                if not channel:
                    raise ValueError("Invalid channel parameter")
            except ValueError as e:
                logger.error(f"Channel validation failed for user {user_id}: {e}")
                embed = gen_error_embed(
                    "Invalid channel parameter.",
                    "Please mention the channels that exist.",
                )
                await ctx.response.send_message(embed=embed)
                return

            try:
                cursor.execute("INSERT INTO users (user_id) VALUES (%s)", (user_id,))
                cursor.execute(
                    "INSERT INTO channels (user_id, channel) VALUES (%s, %s)",
                    (
                        user_id,
                        channel,
                    ),
                )
                conn.commit()
                logger.info(f"Registration completed for user {user_id}")
                embed = discord.Embed(title="Registration completed", color=0x219DDD)
                await ctx.response.send_message(embed=embed)
                return
            except psycopg2.OperationalError as e:
                logger.error(
                    f"Database connection error during registration for user {user_id}: {e}"
                )
                conn.rollback()
                embed = gen_error_embed(
                    "Registration failed due to a database connection issue.",
                    "Please check your database settings and try again later.",
                )
                await ctx.response.send_message(embed=embed)
                return
            except psycopg2.IntegrityError as e:
                logger.error(
                    f"Database integrity error during registration for user {user_id}: {e}"
                )
                conn.rollback()
                embed = gen_error_embed(
                    "Registration failed due to a database integrity issue.",
                    "There may be duplicate entries or other data inconsistencies.",
                )
                await ctx.response.send_message(embed=embed)
                return
            except Exception as e:
                logger.exception(
                    f"Unexpected database error during registration for user {user_id}: {e}"
                )
                conn.rollback()
                embed = gen_error_embed(
                    "Registration failed due to a database error.",
                    "Please try again later or contact the developer.",
                )
                await ctx.response.send_message(embed=embed)
                return

        except Exception as e:
            logger.exception(f"Register failed for user {user_id}: {e}")
            embed = gen_error_embed(
                "An unexpected error occurred.",
                "Please try again later or contact the developer.",
            )
            await ctx.response.send_message(embed=embed)
            return
