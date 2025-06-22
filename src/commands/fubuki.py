import discord
from discord import app_commands
from logging import getLogger, StreamHandler, Formatter, INFO
from views import gen_error_embed

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(INFO)
formatter = Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
handler.setFormatter(formatter)
logger.setLevel(INFO)
logger.addHandler(handler)
logger.propagate = False


def setup(tree):
    @tree.command(name="fubuki", description="こんこんきーつね!!")
    @app_commands.describe(message="？？？")
    async def fubuki(ctx: discord.Interaction, message: str = ""):
        user_id = ctx.user.id
        logger.info(f"/fubuki called by user {user_id}")

        try:
            processed = message.lower()
            if processed in ["nekoyanke", "ねこやんけ", "猫やんけ"]:
                embed = discord.Embed(title="狐じゃい！！ฅ(^`ω´^ฅ§)ﾉ", color=0x53C7EA)
                logger.info(f"User {user_id} triggered 'nekoyanke' response.")
            else:
                embed = discord.Embed(
                    title="こんこんきーつね！(^・ω・^§)ﾉ", color=0x53C7EA
                )
                logger.info(f"User {user_id} triggered default 'fubuki' response.")

            await ctx.response.send_message("🌽" * 32, embed=embed)

        except Exception as e:
            logger.exception(
                f"An error occurred in /fubuki command for user {user_id}: {e}"
            )
            embed = gen_error_embed(
                "An unexpected error occurred.",
                "Please try again later or contact the developer.",
            )
            await ctx.response.send_message(embed=embed)
