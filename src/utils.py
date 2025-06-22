def channel_judge(channel, client):
    if channel[:2] == "<#" and channel[-1] == ">":
        channel = channel[2:-1]
    if channel.isdigit() and client.get_channel(int(channel)):
        return (channel, True)
    else:
        return (channel, False)
