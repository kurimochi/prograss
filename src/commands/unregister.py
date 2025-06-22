import discord
from logger import get_logger
from db import registered
from views import gen_error_embed

logger = get_logger(__name__)


def setup(tree, conn, cursor):
    @tree.command(name="unregister", description="prograssの登録を解除")
    async def unregister(ctx: discord.Interaction):
        user_id = ctx.user.id
        logger.info(f"/unregister called by user {user_id}")

        try:
            try:
                if not registered(user_id, cursor):
                    embed = gen_error_embed(
                        "You are not yet registered.",
                        "If you think this is a mistake, please contact the developer.",
                    )
                    await ctx.response.send_message(embed=embed)
                    logger.info(
                        f"Unregistration: User not registered - no action taken for user {user_id}"
                    )
                    return

                cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
                logger.debug(f"Deleted entry from users table for user_id: {user_id}")

                cursor.execute("DELETE FROM channels WHERE user_id = %s", (user_id,))
                logger.debug(
                    f"Deleted entries from channels table for user_id: {user_id}"
                )

                conn.commit()
                embed = discord.Embed(title="Unregistration completed", color=0x219DDD)
                await ctx.response.send_message(embed=embed)
                logger.info(f"Unregistration completed for user {user_id}")

            except Exception as e:
                logger.exception(f"Unregistration failed for user {user_id}: {e}")
                conn.rollback()
                error_embed = gen_error_embed(
                    "An error occurred during unregistration.",
                    "Please try again later or contact the developer.",
                )
                await ctx.response.send_message(embed=error_embed)

        except Exception as e:
            logger.exception(
                f"Unexpected error during unregistration for user {user_id}: {e}"
            )
            error_embed = gen_error_embed(
                "An unexpected error occurred.",
                "Please try again later or contact the developer.",
            )
            await ctx.response.send_message(embed=error_embed)
