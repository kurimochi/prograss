import discord
from db import registered
from views import gen_error_embed


def setup(tree, conn, cursor):
    @tree.command(name="unregister", description="prograssの登録を解除")
    async def unregister(ctx: discord.Interaction):
        user_id = ctx.user.id
        if registered(user_id, cursor):
            cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
            cursor.execute("DELETE FROM channels WHERE user_id = %s", (user_id,))
            conn.commit()
            embed = discord.Embed(title="Unregistration completed", color=0x219DDD)
        else:
            embed = gen_error_embed(
                "You are not yet registered",
                "If you think this is a mistake, please contact the developer",
            )
        await ctx.response.send_message(embed=embed)
