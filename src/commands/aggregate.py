import discord
from db import registered, aggr_internal
from views import gen_error_embed


def setup(tree, cursor):
    @tree.command(
        name="aggregate", description="今日00:00から現時点までの進捗一覧を表示"
    )
    async def aggregate(ctx: discord.Interaction):
        user_id = ctx.user.id
        if registered(user_id, cursor):
            progress = aggr_internal(user_id, cursor)
            if not progress:
                embed = discord.Embed(
                    title="現時点での進捗はありません", color=0xFA8000
                )
            else:
                embed = discord.Embed(title="現時点での進捗一覧", color=0x219DDD)
                embed.set_author(name=ctx.user.name, icon_url=ctx.user.avatar.url)
                embed.add_field(
                    name="",
                    value="\n".join([f"{i+1}. {p}" for i, p in enumerate(progress)]),
                )
        else:
            embed = gen_error_embed(
                "You are not yet registered", "Please register using /register"
            )
        await ctx.response.send_message(embed=embed)
