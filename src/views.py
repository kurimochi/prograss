import discord


def gen_error_embed(details, approach, info={}):
    embed = discord.Embed(title="Error!", color=0xBF1E33)
    embed.add_field(name="Details", value=details)
    embed.add_field(name="Approach", value=approach)
    if info:
        keys = list(info.keys())
        if keys:
            max_key_length = max(len(key) for key in keys)
            embed.add_field(
                name="Info",
                value="```"
                + "".join(
                    [
                        f"{key:<{max_key_length}}: {value}\n"
                        for key, value in info.items()
                    ]
                )
                + "```",
                inline=False,
            )
    return embed
