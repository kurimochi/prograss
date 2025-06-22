import discord
from logger import get_logger
from logic import send_error_with_remove
from views import gen_error_embed

logger = get_logger(__name__)


def setup(tree, conn, cursor, client):
    @tree.command(name="showconf", description="現在の設定を表示")
    async def showconf(ctx: discord.Interaction):
        user_id = ctx.user.id
        embed = discord.Embed(title="設定一覧", color=0xA0A0A0)

        try:
            cursor.execute(
                "SELECT channel FROM channels WHERE user_id = %s", (user_id,)
            )
            channels = []
            for c in cursor.fetchall():
                channel_id = c[0]
                channel_obj = client.get_channel(channel_id)

                if channel_obj is None:
                    await send_error_with_remove(
                        ctx.user,
                        channel_id,
                        (
                            "The channel you set up has been deleted",
                            "Please change channel with /config",
                        ),
                        {"Channel_ID": channel_id},
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
            logger.info(f"showconf command executed successfully for user {user_id}")

        except Exception as e:
            logger.exception(
                f"Error executing showconf command for user {user_id}: {e}"
            )
            error_embed = error_embed = gen_error_embed(
                "An error occurred during unregistration.",
                "Please try again later or contact the developer.",
            )
            await ctx.response.send_message(embed=error_embed, ephemeral=True)
