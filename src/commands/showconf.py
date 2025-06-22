import discord
from logic import send_error_with_remove


def setup(tree, conn, cursor, client):
    @tree.command(name="showconf", description="現在の設定を表示")
    async def showconf(ctx: discord.Interaction):
        user_id = ctx.user.id
        embed = discord.Embed(title="設定一覧", color=0xA0A0A0)
        cursor.execute("SELECT channel FROM channels WHERE user_id = %s", (user_id,))
        channels = []
        for c in cursor.fetchall():
            channel_obj = client.get_channel(c[0])
            if channel_obj is None:
                await send_error_with_remove(
                    ctx.user,
                    c[0],
                    (
                        "The channel you set up has been deleted",
                        "Please change channel with /config",
                    ),
                    {"Channel_ID": c[0]},
                    conn,
                    cursor,
                )
                continue
            channels.append(f"{channel_obj.guild.name} / {channel_obj.name}")
        embed.add_field(
            name="channel",
            value="\n".join([f"{i+1}. {c}" for i, c in enumerate(channels)])
            or "No channel set",
        )
        cursor.execute("SELECT notice FROM users WHERE user_id = %s", (user_id,))
        notice = cursor.fetchone()
        embed.add_field(
            name="notice", value=notice[0] if notice and notice[0] else "No notice"
        )
        await ctx.response.send_message(embed=embed, ephemeral=True)
