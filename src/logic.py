import discord
from logger import get_logger
from views import gen_error_embed

logger = get_logger(__name__)


async def send_channel_message(user, channel, channel_id, text, embed, conn, cursor):
    try:
        msg = await channel.send(text, embed=embed)
        logger.info(f"Message sent to channel {channel_id} for user {user.id}")
        return msg
    except AttributeError as e:
        logger.warning(
            f"Channel {channel_id} is inaccessible or deleted for user {user.id}. Error: {e}"
        )
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
    except discord.errors.Forbidden as e:
        logger.warning(
            f"Forbidden to send message to channel {channel_id} for user {user.id}. Error: {e}"
        )
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
        logger.exception(f"Send failed for channel {channel_id} user {user.id}: {e}")
        logger.exception("Full traceback:")
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
    logger.info(
        f"send_error_with_remove called for user={getattr(user, 'id', None)} channel={channel_id} msg={msg} info={info}"
    )
    try:
        error_embed = gen_error_embed(*msg, info)
        view = discord.ui.View()

        async def remove_channel_callback(ctx: discord.Interaction):
            try:
                cursor.execute(
                    "DELETE FROM channels WHERE user_id = %s AND channel = %s",
                    (user.id, channel_id),
                )
                conn.commit()
                error_embed2 = gen_error_embed(
                    *msg, {**info, "Status": "Channel config have been changed"}
                )
                await ctx.response.edit_message(embed=error_embed2, view=None)
            except Exception as e:
                logger.exception(
                    f"Failed to remove channel for user {user.id} and channel {channel_id}: {e}"
                )

        remove_button = discord.ui.Button(
            label="Remove this channel from config", style=discord.ButtonStyle.danger
        )
        remove_button.callback = remove_channel_callback
        view.add_item(remove_button)
        try:
            await user.send(embed=error_embed, view=view)
            logger.info(
                f"Error notification sent to user={getattr(user, 'id', None)} channel={channel_id}"
            )
        except discord.errors.Forbidden:
            logger.warning(
                f"Could not send error message to user {user.id}. User may have DMs disabled."
            )

    except Exception as e:
        logger.exception(
            f"Failed to send error notification to user={getattr(user, 'id', None)} channel={channel_id}: {e}"
        )
