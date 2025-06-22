import discord
from discord import app_commands


def setup(tree):
    @tree.command(name="fubuki", description="こんこんきーつね!!")
    @app_commands.describe(message="？？？")
    async def fubuki(ctx: discord.Interaction, message: str = ""):
        processed = message.lower()
        if processed in ["nekoyanke", "ねこやんけ", "猫やんけ"]:
            embed = discord.Embed(title="狐じゃい！！ฅ(^`ω´^ฅ§)ﾉ", color=0x53C7EA)
        else:
            embed = discord.Embed(title="こんこんきーつね！(^・ω・^§)ﾉ", color=0x53C7EA)
        await ctx.response.send_message("🌽" * 32, embed=embed)
