from logger import get_logger

logger = get_logger(__name__)


def channel_judge(channel, client):
    try:
        if channel[:2] == "<#":
            channel = channel[2:-1]

        if channel.isdigit():
            channel_id = int(channel)
            if client.get_channel(channel_id):
                return channel_id
            else:
                logger.warning(f"Channel with ID {channel_id} not found.")
                return None
        else:
            logger.warning(f"Channel name {channel} is not a valid ID.")
            return None

    except ValueError:
        logger.error(f"Invalid channel format: {channel}")
        return None
    except Exception as e:
        logger.exception(
            f"An unexpected error occurred while validating the channel: {e}"
        )
        return None
