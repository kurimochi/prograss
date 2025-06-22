import discord
from logger import get_logger

logger = get_logger(__name__)


def gen_error_embed(details, approach, info={}):
    try:
        embed = discord.Embed(title="Error!", color=0xBF1E33)
        embed.add_field(name="Details", value=details)
        embed.add_field(name="Approach", value=approach)

        if info:
            keys = list(info.keys())
            if keys:
                max_key_length = max(len(key) for key in keys)
                info_string = "".join(
                    [
                        f"{key:<{max_key_length}}: {value}\n"
                        for key, value in info.items()
                    ]
                )
                embed.add_field(
                    name="Info", value="```" + info_string + "```", inline=False
                )

        return embed
    except Exception as e:
        logger.exception(f"Error generating error embed: {e}")
        raise
