from logging import getLogger, StreamHandler, Formatter, INFO

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(INFO)
formatter = Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
handler.setFormatter(formatter)
logger.setLevel(INFO)
logger.addHandler(handler)
logger.propagate = False


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
