import discord
from views import gen_error_embed


async def send_channel_message(user, channel, channel_id, text, embed, conn, cursor):
    try:
        await channel.send(text, embed=embed)
    except AttributeError:
        await send_error_with_remove(
            user,
            channel_id,
            (
                "The channel you set up is inaccessible or has been deleted",
                "Please change channel with /config",
            ),
            {
                "Server": channel.guild.name if channel else "Unknown",
                "Channel": channel_id,
            },
            conn,
            cursor,
        )
    except discord.errors.Forbidden:
        await send_error_with_remove(
            user,
            channel_id,
            (
                "Message cannot be sent on this channel",
                "Please set up a channel for possible transmission or contact your server administrator",
            ),
            {
                "Server": channel.guild.name if channel else "Unknown",
                "Channel": channel_id,
            },
            conn,
            cursor,
        )
    except Exception as e:
        print(f"Send failed: {type(e)} {repr(e)}")
        await send_error_with_remove(
            user,
            channel_id,
            ("An unexpected error has occurred", "Please contact the developer"),
            {
                "Server": channel.guild.name if channel else "Unknown",
                "Channel": channel_id,
                "Error": str(e),
            },
            conn,
            cursor,
        )


async def send_error_with_remove(user, channel_id, msg, info, conn, cursor):
    error_embed = gen_error_embed(*msg, info)
    view = discord.ui.View()

    async def remove_channel_callback(ctx: discord.Interaction):
        cursor.execute(
            "DELETE FROM channels WHERE user_id = %s AND channel = %s",
            (user.id, channel_id),
        )
        conn.commit()
        error_embed2 = gen_error_embed(
            *msg, {**info, "Status": "Channel config have been changed"}
        )
        await ctx.response.edit_message(embed=error_embed2, view=None)

    remove_button = discord.ui.Button(
        label="Remove this channel from config", style=discord.ButtonStyle.danger
    )
    remove_button.callback = remove_channel_callback
    view.add_item(remove_button)
    await user.send(embed=error_embed, view=view)
