import discord
from discord import app_commands
from db import registered
from views import gen_error_embed


def setup(tree, conn, cursor):
    @tree.command(name="submit", description="進捗を登録")
    @app_commands.describe(progress="進捗内容")
    async def submit(ctx: discord.Interaction, progress: str):
        user_id = ctx.user.id
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
        else:
            embed = gen_error_embed(
                "You are not yet registered", "Please register using /register"
            )
        await ctx.response.send_message(embed=embed)
