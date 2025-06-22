import discord
import asyncio
from discord.ext import tasks
from datetime import datetime
from db import aggr_internal
from logic import send_channel_message


def setup_cron(conn, cursor, client):
    @tasks.loop(seconds=60)
    async def cron():
        now = datetime.now().strftime("%H:%M")
        cursor.execute("SELECT user_id, notice FROM users")
        users = cursor.fetchall()
        # 進捗送信（00:00のみ）
        if now == "00:00":
            cursor.execute("SELECT user_id FROM users")
            user_ids = [u[0] for u in cursor.fetchall()]

            async def send_progress(user_id):
                progress = aggr_internal(user_id, cursor)
                user = await client.fetch_user(user_id)
                if not progress:
                    return
                embed = discord.Embed(title="今日の進捗", color=0xB9C42F)
                embed.set_author(name=user.name, icon_url=user.avatar.url)
                embed.add_field(
                    name="",
                    value="\n".join([f"{i+1}. {p}" for i, p in enumerate(progress)]),
                )
                text = f"<@{user_id}>"
                cursor.execute(
                    "SELECT channel FROM channels WHERE user_id = %s", (user_id,)
                )
                channels = [c[0] for c in cursor.fetchall()]
                for channel_id in channels:
                    channel = client.get_channel(channel_id)
                    await send_channel_message(
                        user, channel, channel_id, text, embed, conn, cursor
                    )
                # バックアップ・削除
                cursor.execute(
                    "SELECT message, timestamp FROM progress WHERE user_id = %s",
                    (user_id,),
                )
                for message, timestamp in cursor.fetchall():
                    cursor.execute(
                        "INSERT INTO backup_progress (user_id, message, timestamp) VALUES (%s, %s, %s)",
                        (
                            user_id,
                            message,
                            timestamp,
                        ),
                    )
                cursor.execute("DELETE FROM progress WHERE user_id = %s", (user_id,))
                conn.commit()

            await asyncio.gather(*(send_progress(uid) for uid in user_ids))

        # 通知処理
        async def notice(user_id, notice_time):
            if notice_time and now == notice_time:
                if not aggr_internal(user_id, cursor):
                    user = await client.fetch_user(user_id)
                    embed = discord.Embed(
                        title="|　 | ∧_,∧\n|＿|( ´∀`)＜進捗ぬるぽ\n|柱|　⊂ ﾉ\n|￣|―ｕ'",
                        color=0xB92946,
                    )
                    embed.set_author(name=user.name, icon_url=user.avatar.url)
                    embed.add_field(
                        name="",
                        value=f"```　　　Λ＿Λ　　＼＼\n　 （　・∀・）　　　|　|　ｶﾞｯ\n　と　　　　）　 　 |　|\n　　 Ｙ　/ノ　　　 人\n　　　 /　）　 　 < 　>_Λ∩\n　　 ＿/し'　／／. Ｖ｀Д´）/\n　（＿フ彡　　　　　 　　/　←>>{user.name}\n```",
                    )
                    text = f"<@{user_id}>\n"
                    cursor.execute(
                        "SELECT channel FROM channels WHERE user_id = %s", (user_id,)
                    )
                    channels = [c[0] for c in cursor.fetchall()]
                    for channel_id in channels:
                        channel = client.get_channel(channel_id)
                        await send_channel_message(
                            user, channel, channel_id, text, embed, conn, cursor
                        )

        await asyncio.gather(*(notice(u[0], u[1]) for u in users))

    return cron
