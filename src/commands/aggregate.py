import discord
from logging import getLogger, StreamHandler, Formatter, INFO
from db import registered, aggr_internal
from views import gen_error_embed

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(INFO)
formatter = Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
handler.setFormatter(formatter)
logger.setLevel(INFO)
logger.addHandler(handler)
logger.propagate = False


def setup(tree, cursor):
    @tree.command(
        name="aggregate", description="今日00:00から現時点までの進捗一覧を表示"
    )
    async def aggregate(ctx: discord.Interaction):
        user_id = ctx.user.id
        logger.info(f"/aggregate called by user {user_id}")

        try:
            if registered(user_id, cursor):
                progress = aggr_internal(user_id, cursor)
                if not progress:
                    embed = discord.Embed(
                        title="現時点での進捗はありません", color=0xFA8000
                    )
                    logger.info(f"No progress found for user {user_id}")
                else:
                    embed = discord.Embed(title="現時点での進捗一覧", color=0x219DDD)
                    embed.set_author(name=ctx.user.name, icon_url=ctx.user.avatar.url)
                    embed.add_field(
                        name="",
                        value="\n".join(
                            [f"{i+1}. {p}" for i, p in enumerate(progress)]
                        ),
                    )
                    logger.info(f"Progress retrieved for user {user_id}: {progress}")
            else:
                embed = gen_error_embed(
                    "You are not yet registered.", "Please register using /register."
                )
                logger.warning(f"User {user_id} is not registered.")

        except Exception as e:
            logger.exception(
                f"An error occurred while retrieving progress for user {user_id}: {e}"
            )
            embed = gen_error_embed(
                "An unexpected error occurred.",
                "Please try again later or contact the developer.",
            )

        await ctx.response.send_message(embed=embed)
