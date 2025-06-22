import discord
import psycopg2
import asyncio
import re
import os
import time
from discord import app_commands
from discord.ext import tasks
from datetime import datetime

TOKEN = os.getenv('TOKEN')
DB_NAME = os.getenv('POSTGRES_DB')
DB_USER = os.getenv('POSTGRES_USER')
DB_PASS = os.getenv('POSTGRES_PASSWORD')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# DB初期化
for i in range(10):
    try:
        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host='db')
        break
    except psycopg2.OperationalError as e:
        print(f'DB connection failed, retry... ({i+1}/10)')
        time.sleep(3)
else:
    raise Exception('Could not connect to PostgreSQL.')

cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS progress (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        message TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        notice TEXT
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS channels (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        channel BIGINT NOT NULL
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS votes (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        message_id BIGINT NOT NULL,
        consent INTEGER NOT NULL,
        refusal INTEGER NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS backup_progress (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        message TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()

def gen_error_embed(details, approach, info={}):
    embed = discord.Embed(
        title='Error!',
        color=0xbf1e33
    )
    embed.add_field(name='Details', value=details)
    embed.add_field(name='Approach', value=approach)

    if info:
        keys = list(info.keys())
        if keys:
            max_key_length = max(len(key) for key in keys)
            embed.add_field(
                name='Info',
                value='```' + ''.join([f'{key:<{max_key_length}}: {value}\n' for key, value in info.items()]) + '```',
                inline=False
            )

    return embed

# ユーザーが登録しているかを判定
def registered(user_id):
    cursor.execute('SELECT user_id FROM users WHERE user_id = %s', (user_id,))
    result = cursor.fetchone()

    if result is None:
        return False
    else:
        return True

# channel設定が正当かを判定
def channel_judge(channel):
    if channel[:2] == '<#' and channel[-1] == '>':
        channel = channel[2:-1]

    if channel.isdigit() and client.get_channel(int(channel)):
        return (channel, True)
    else:
        return (channel, False)

# aggregate内のprogress取得
def aggr_internal(user_id):
    cursor.execute('SELECT message FROM progress WHERE user_id = %s', (user_id,))
    progress = cursor.fetchall()
    return progress

# bot初期化
@client.event
async def on_ready():
    print('Bot is ready.')
    cron.start()
    await tree.sync()

# /register  prograssに登録
@tree.command(name='register', description='prograssに登録')
@app_commands.describe(channel='定期メッセージを送信するチャンネル (メンション or ID)')
async def register(ctx: discord.Interaction, channel: str):
    user_id = ctx.user.id

    if registered(user_id):
        embed = gen_error_embed('You are already registered', 'If you think this is a mistake, please contact the developer')
    else:
        channel, judge = channel_judge(channel)
        if judge:
            cursor.execute('INSERT INTO users (user_id) VALUES (%s)', (user_id,))
            cursor.execute('INSERT INTO channels (user_id, channel) VALUES (%s, %s)', (user_id, channel,))
            conn.commit()
            embed = discord.Embed(
                title='Registration completed',
                color=0x219ddd
            )
        else:
            embed = gen_error_embed('Invalid channel parameter', 'Please mention the channels that exist')

    await ctx.response.send_message(embed=embed)

# /unregister  prograssの登録を解除
@tree.command(name='unregister', description='prograssの登録を解除')
async def unregister(ctx: discord.Interaction):
    user_id = ctx.user.id

    if registered(user_id):
        cursor.execute('DELETE FROM users WHERE user_id = %s', (user_id,))
        cursor.execute('DELETE FROM channels WHERE user_id = %s', (user_id,))
        conn.commit()
        embed = discord.Embed(
            title='Unregistration completed',
            color=0x219ddd
        )
    else:
        embed = gen_error_embed('You are not yet registered', 'If you think this is a mistake, please contact the developer')

    await ctx.response.send_message(embed=embed)

# /submit  進捗を登録する
@tree.command(name='submit', description='進捗を登録')
@app_commands.describe(progress='進捗内容')
async def submit(ctx: discord.Interaction, progress: str):
    user_id = ctx.user.id

    if registered(user_id):
        cursor.execute('INSERT INTO progress (user_id, message) VALUES (%s, %s)', (user_id, progress,))
        conn.commit()
        embed = discord.Embed(
            title='Progress was submitted',
            color=0x219ddd
        )
        embed.add_field(name='Progress:', value=progress)
    else:
        embed = gen_error_embed('You are not yet registered', 'Please register using /register')
    await ctx.response.send_message(embed=embed)

# /config  ユーザーごとの設定を変更
@tree.command(name='config', description='設定を変更')
@app_commands.describe(key='変更する項目', value='変更後の値 (channel -> チャンネルをメンション  notice -> HH:MM)')
@app_commands.choices(key=[
    app_commands.Choice(name='channel', value='channel'),
    app_commands.Choice(name='notice', value='notice')
])
async def config(ctx: discord.Interaction, key: str, value: str):
    if registered(ctx.user.id):
        if key == 'channel':
            channel, judge = channel_judge(value)
            if judge:
                cursor.execute('SELECT channel FROM channels WHERE user_id = %s AND channel = %s', (ctx.user.id, channel,))
                if cursor.fetchall() == []:
                    # 追加処理
                    cursor.execute('INSERT INTO channels (user_id, channel) VALUES (%s, %s)', (ctx.user.id, channel,))
                    conn.commit()
                    embed = discord.Embed(
                        title='Channel config have been successfully updated',
                        color=0x219ddd
                    )
                else:
                    # 削除処理
                    cursor.execute('SELECT channel FROM channels WHERE user_id = %s AND channel != %s', (ctx.user.id, channel,))
                    if cursor.fetchall() != []:
                        cursor.execute('DELETE FROM channels WHERE user_id = %s AND channel = %s', (ctx.user.id, channel,))
                        conn.commit()
                        embed = discord.Embed(
                            title='Channel config have been successfully updated',
                            color=0x219ddd
                        )
                    else:
                        embed = gen_error_embed('Too few channels set', 'Add 1 or more channels')
            else:
                embed = gen_error_embed('Invalid channel parameter', 'Please mention the channels that exist')

        elif key == 'notice':
            if re.fullmatch(r'[0-9]:[0-5][0-9]', value):
                value = f'0{value}'
            elif not re.fullmatch(r'([01][0-9]|2[0-3]):[0-5][0-9]', value):
                value = ''
            cursor.execute('UPDATE users SET notice = %s WHERE user_id = %s', (value, ctx.user.id,))
            conn.commit()
            embed = discord.Embed(
                title='Notice config have been successfully updated',
                color=0x219ddd
            )
            embed.add_field(name='New config:', value='No notice' if value == '' else value)
        else:
            embed = gen_error_embed('A key that does not exist', 'Please specify a key that exists')

    else:
        embed = discord.Embed(
            title='Error!',
            color=0xbf1e33
        )
        embed = gen_error_embed('You are not yet registered', 'Please register using /register')

    await ctx.response.send_message(embed=embed, ephemeral=True)

# /showconf  設定一覧を出力
@tree.command(name='showconf', description='現在の設定を表示')
async def showconf(ctx: discord.Interaction):
    embed = discord.Embed(
        title='設定一覧',
        color=0xa0a0a0
    )
    cursor.execute('SELECT channel FROM channels WHERE user_id = %s', (ctx.user.id,))
    channels = []
    for c in cursor.fetchall():
        channel = client.get_channel(c[0])
        if channel is None:
            error_embed = gen_error_embed(
                'The channel you set up has been deleted',
                'Please change channel with /config',
                {'Channel_ID': c[0]}
            )
            view = discord.ui.View()
            async def remove_channel_callback(ctx: discord.Interaction):
                cursor.execute('DELETE FROM channels WHERE user_id = %s AND channel = %s', (ctx.user.id, c[0]))
                conn.commit()
                error_embed = gen_error_embed(
                    'The channel you set up has been deleted',
                    'Channel config have been changed',
                    {'Channel_ID': c[0]}
                )
                await ctx.response.edit_message(embed=error_embed, view=None)
            remove_button = discord.ui.Button(label='Remove this channel from config', style=discord.ButtonStyle.danger)
            remove_button.callback = remove_channel_callback
            view.add_item(remove_button)
            await ctx.user.send(embed=error_embed, view=view)
            continue
        channels.append([channel.guild.name, channel.name])

    embed.add_field(name='channel', value=''.join([f'1. {c[0]} / {c[1]}\n' for c in channels]))
    cursor.execute('SELECT notice FROM users WHERE user_id = %s', (ctx.user.id,))
    notice = cursor.fetchone()[0]
    embed.add_field(name='notice', value=notice if notice else 'No notice')

    await ctx.response.send_message(embed=embed, ephemeral=True)

# /fubuki  こんこんきーつね!!
@tree.command(name='fubuki', description='こんこんきーつね!!')
@app_commands.describe(message='？？？')
async def fubuki(ctx: discord.Interaction, message: str = ''):
    processed = message.lower()
    match processed:
        case 'nekoyanke' | 'ねこやんけ' | '猫やんけ':
            embed = discord.Embed(
                title='狐じゃい！！ฅ(^`ω´^ฅ§)ﾉ',
                color=0x53c7ea
            )
        case _:
            embed = discord.Embed(
                title='こんこんきーつね！(^・ω・^§)ﾉ',
                color=0x53c7ea
            )
    await ctx.response.send_message('🌽'*32, embed=embed)

# /aggregate  現時点での進捗一覧
@tree.command(name='aggregate', description='今日00:00から現時点までの進捗一覧を表示')
async def aggregate(ctx: discord.Interaction):
    if registered(ctx.user.id):
        progress = aggr_internal(ctx.user.id)

        if progress == []:
            embed = discord.Embed(
                title='現時点での進捗はありません',
                color=0xfa8000,
            )
        else:
            embed = discord.Embed(
                title='現時点での進捗一覧',
                color=0x219ddd
            )
            embed.set_author(
                name=ctx.user.name,
                icon_url=ctx.user.avatar.url
            )
            embed.add_field(name='', value=''.join([f'1. {p[0]}\n' for p in progress]))
    else:
        embed = gen_error_embed('You are not yet registered', 'Please register using /register')

    await ctx.response.send_message(embed=embed)

@tasks.loop(seconds=60)
async def cron():
    now = datetime.now().strftime('%H:%M')
    # aggregateの定時処理・投票処理
    if now == '00:00':
        cursor.execute('SELECT user_id FROM users')
        users = cursor.fetchall()

        async def send_progress(user_id):
            # 進捗送信
            progress = aggr_internal(user_id)
            user = await client.fetch_user(user_id)
            embed = discord.Embed(
                title='今日の進捗',
                color=0xb9c42f
            )
            embed.set_author(
                name=user.name,
                icon_url=user.avatar.url
            )
            embed.add_field(name='', value=''.join([f'1. {p[0]}\n' for p in progress]))
            text = f'<@{user_id}>'

            async def send(channel_id):
                channel = client.get_channel(channel_id)
                try:
                    await channel.send(text, embed=embed)
                except AttributeError:
                    error_embed = gen_error_embed(
                        'The channel you set up is inaccessible or has been deleted',
                        'Please change channel with /config',
                        {'Server': channel.guild.name if channel else 'Unknown', 'Channel': channel_id}
                    )
                    await user.send(embed=error_embed)
                    view = discord.ui.View()
                    async def remove_channel_callback(ctx: discord.Interaction):
                        cursor.execute('DELETE FROM channels WHERE user_id = %s AND channel = %s', (user_id, channel_id))
                        conn.commit()
                        error_embed = gen_error_embed(
                            'The channel you set up is inaccessible or has been deleted',
                            'Channel config have been changed',
                            {'Server': channel.guild.name if channel else 'Unknown', 'Channel': channel_id}
                        )
                        await ctx.response.edit_message(embed=error_embed, view=None)
                    remove_button = discord.ui.Button(label='Remove this channel from config', style=discord.ButtonStyle.danger)
                    remove_button.callback = remove_channel_callback
                    view.add_item(remove_button)
                    await user.send(embed=error_embed, view=view)
                except discord.errors.Forbidden:
                    error_embed = gen_error_embed(
                        'Message cannot be sent on this channel',
                        'Please set up a channel for possible transmission or contact your server administrator',
                        {'Server': channel.guild.name if channel else 'Unknown', 'Channel': channel_id}
                    )
                    view = discord.ui.View()
                    async def remove_channel_callback(ctx: discord.Interaction):
                        cursor.execute('DELETE FROM channels WHERE user_id = %s AND channel = %s', (user_id, channel_id))
                        conn.commit()
                        error_embed = gen_error_embed(
                            'Message cannot be sent on this channel',
                            'Channel config have been changed',
                            {'Server': channel.guild.name if channel else 'Unknown', 'Channel': channel_id}
                        )
                        await ctx.response.edit_message(embed=error_embed, view=None)
                    remove_button = discord.ui.Button(label='Remove this channel from config', style=discord.ButtonStyle.danger)
                    remove_button.callback = remove_channel_callback
                    view.add_item(remove_button)
                    await user.send(embed=error_embed, view=view)
                except Exception as e:
                    print(f'Send failed: {type(e)} {repr(e)}')
                    error_embed = gen_error_embed(
                        'An unexpected error has occurred',
                        'Please contact the developer',
                        {'Server': channel.guild.name if channel else 'Unknown', 'Channel': channel_id}
                    )
                    await user.send(embed=error_embed)
                    view = discord.ui.View()
                    async def remove_channel_callback(ctx: discord.Interaction):
                        cursor.execute('DELETE FROM channels WHERE user_id = %s AND channel = %s', (user_id, channel_id))
                        conn.commit()
                        error_embed = gen_error_embed(
                            'An unexpected error has occurred',
                            'Channel config have been changed',
                            {'Server': channel.guild.name if channel else 'Unknown', 'Channel': channel_id}
                        )
                        await ctx.response.edit_message(embed=error_embed, view=None)
                    remove_button = discord.ui.Button(label='Remove this channel from config', style=discord.ButtonStyle.danger)
                    remove_button.callback = remove_channel_callback
                    view.add_item(remove_button)
                    await user.send(embed=error_embed, view=view)

            cursor.execute('SELECT channel FROM channels WHERE user_id = %s', (user_id,))
            for c in cursor.fetchall():
                asyncio.create_task(send(c[0]))

            # バックアップ・削除
            cursor.execute('SELECT message, timestamp FROM progress WHERE user_id = %s', (user_id,))
            for message, timestamp in cursor.fetchall():
                cursor.execute('INSERT INTO backup_progress (user_id, message, timestamp) VALUES (%s, %s, %s)', (user_id, message, timestamp,))
            cursor.execute('DELETE FROM progress WHERE user_id = %s', (user_id,))
            conn.commit()

            # 投票作成
            await msg.add_reaction('👍')
            await msg.add_reaction('👎')
            await asyncio.sleep(86400)
            # 投票集計
            msg = await msg.channel.fetch_message(msg.id)
            consent = discord.utils.get(msg.reactions, emoji='👍').count - 1
            refusal = discord.utils.get(msg.reactions, emoji='👎').count - 1
            cursor.execute('INSERT INTO votes (user_id, message_id, consent, refusal) VALUES (%s, %s, %s, %s)', (user_id, msg.id, consent, refusal))
            conn.commit()

        for u in users:
            asyncio.create_task(send_progress(u[0]))

    # 通知処理
    async def notice(user_id):
        cursor.execute('SELECT notice FROM users WHERE user_id = %s', (user_id,))
        notice_result = cursor.fetchone()
        if notice_result and now == notice_result[0]:
            if aggr_internal(user_id) == []:
                embed = discord.Embed(
                    title='|　 | ∧_,∧\n|＿|( ´∀`)＜進捗ぬるぽ\n|柱|　⊂ ﾉ\n|￣|―ｕ\'',
                    color=0xb92946
                )
                user = await client.fetch_user(user_id)
                embed.set_author(
                    name=user.name,
                    icon_url=user.avatar.url
                )
                embed.add_field(
                    name='',
                    value=f'```　　　Λ＿Λ　　＼＼\n　 （　・∀・）　　　|　|　ｶﾞｯ\n　と　　　　）　 　 |　|\n　　 Ｙ　/ノ　　　 人\n　　　 /　）　 　 < 　>_Λ∩\n　　 ＿/し\'　／／. Ｖ｀Д´）/\n　（＿フ彡　　　　　 　　/　←>>{user.name}\n```')
                text = f'<@{user_id}>\n'

                async def send(channel_id):
                    channel = client.get_channel(channel_id)
                    try:
                        await channel.send(text, embed=embed)
                    except AttributeError:
                        error_embed = gen_error_embed(
                            'The channel you set up is inaccessible or has been deleted',
                            'Please change channel with /config',
                            {'Server': channel.guild.name if channel else 'Unknown', 'Channel': channel_id}
                        )
                        await user.send(embed=error_embed)
                        view = discord.ui.View()
                        async def remove_channel_callback(ctx: discord.Interaction):
                            cursor.execute('DELETE FROM channels WHERE user_id = %s AND channel = %s', (user_id, channel_id))
                            conn.commit()
                            error_embed = gen_error_embed(
                                'The channel you set up is inaccessible or has been deleted',
                                'Channel config have been changed',
                                {'Server': channel.guild.name if channel else 'Unknown', 'Channel': channel_id}
                            )
                            await ctx.response.edit_message(embed=error_embed, view=None)
                        remove_button = discord.ui.Button(label='Remove this channel from config', style=discord.ButtonStyle.danger)
                        remove_button.callback = remove_channel_callback
                        view.add_item(remove_button)
                        await user.send(embed=error_embed, view=view)
                    except discord.errors.Forbidden:
                        error_embed = gen_error_embed(
                            'Message cannot be sent on this channel',
                            'Please set up a channel for possible transmission or contact your server administrator',
                            {'Server': channel.guild.name if channel else 'Unknown', 'Channel': channel_id}
                        )
                        view = discord.ui.View()
                        async def remove_channel_callback(ctx: discord.Interaction):
                            cursor.execute('DELETE FROM channels WHERE user_id = %s AND channel = %s', (user_id, channel_id))
                            conn.commit()
                            error_embed = gen_error_embed(
                                'Message cannot be sent on this channel',
                                'Channel config have been changed',
                                {'Server': channel.guild.name if channel else 'Unknown', 'Channel': channel_id}
                            )
                            await ctx.response.edit_message(embed=error_embed, view=None)
                        remove_button = discord.ui.Button(label='Remove this channel from config', style=discord.ButtonStyle.danger)
                        remove_button.callback = remove_channel_callback
                        view.add_item(remove_button)
                        await user.send(embed=error_embed, view=view)
                    except Exception as e:
                        print(f'Send failed: {type(e)} {repr(e)}')
                        error_embed = gen_error_embed(
                            'An unexpected error has occurred',
                            'Please contact the developer',
                            {'Server': channel.guild.name if channel else 'Unknown', 'Channel': channel_id}
                        )
                        await user.send(embed=error_embed)
                        view = discord.ui.View()
                        async def remove_channel_callback(ctx: discord.Interaction):
                            cursor.execute('DELETE FROM channels WHERE user_id = %s AND channel = %s', (user_id, channel_id))
                            conn.commit()
                            error_embed = gen_error_embed(
                                'An unexpected error has occurred',
                                'Channel config have been changed',
                                {'Server': channel.guild.name if channel else 'Unknown', 'Channel': channel_id}
                            )
                            await ctx.response.edit_message(embed=error_embed, view=None)
                        remove_button = discord.ui.Button(label='Remove this channel from config', style=discord.ButtonStyle.danger)
                        remove_button.callback = remove_channel_callback
                        view.add_item(remove_button)
                        await user.send(embed=error_embed, view=view)

                cursor.execute('SELECT channel FROM channels WHERE user_id = %s', (user_id,))
                for c in cursor.fetchall():
                    asyncio.create_task(send(c[0]))

    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    for u in users:
        asyncio.create_task(notice(u[0]))

# Botの起動とDiscordサーバーへの接続
client.run(TOKEN)