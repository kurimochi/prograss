import discord
from discord import app_commands
from logging import getLogger, StreamHandler, Formatter, INFO
from db import registered
from views import gen_error_embed

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(INFO)
formatter = Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
handler.setFormatter(formatter)
logger.setLevel(INFO)
logger.addHandler(handler)
logger.propagate = False


def setup(tree, conn, cursor):
    @tree.command(name="submit", description="進捗を登録")
    @app_commands.describe(progress="進捗内容")
    async def submit(ctx: discord.Interaction, progress: str):
        user_id = ctx.user.id
        logger.info(f"/submit called by user {user_id} with progress: {progress}")

        try:
            if registered(user_id, cursor):
                cursor.execute(
                    "INSERT INTO progress (user_id, message) VALUES (%s, %s)",
                    (
                        user_id,
                        progress,
                    ),
                )
                conn.commit()
                embed = discord.Embed(title="Progress was submitted", color=0x219DDD)
                embed.add_field(name="Progress:", value=progress)
                await ctx.response.send_message(embed=embed)
                logger.info(f"Successfully submitted progress for user {user_id}")

            else:
                embed = gen_error_embed(
                    "You are not yet registered.", "Please register using /register."
                )
                await ctx.response.send_message(embed=embed)
                logger.warning(
                    f"User {user_id} is not registered, cannot submit progress."
                )

        except Exception as e:
            logger.exception(f"Error submitting progress for user {user_id}: {e}")
            error_embed = gen_error_embed(
                "An unexpected error occurred.",
                "Please try again later or contact the developer.",
            )
            await ctx.response.send_message(embed=error_embed)
