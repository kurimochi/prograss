import asyncio
from datetime import datetime
from discord import Embed, utils
from discord.ext import tasks
from logger import get_logger
from db import aggr_internal
from logic import send_channel_message

logger = get_logger(__name__)


async def setup_cron(conn, cursor, client):
    @tasks.loop(seconds=60)
    async def cron():
        now = datetime.now().strftime("%H:%M")
        logger.info(f"[cron] tick: {now}")

        if now == "00:00":
            try:
                cursor.execute("SELECT user_id FROM users")
                user_ids = [u[0] for u in cursor.fetchall()]
                logger.info(
                    f"[cron] Retrieved {len(user_ids)} user(s) for progress check"
                )

                async def send_progress(user_id):
                    try:
                        logger.debug(f"[cron] Processing progress for user {user_id}")
                        progress = aggr_internal(user_id, cursor)
                        if not progress:
                            logger.info(
                                f"[cron] No progress to send for user {user_id}"
                            )
                            return

                        user = await client.fetch_user(user_id)
                        logger.debug(f"[cron] Fetched user object for {user_id}")

                        embed = Embed(title="今日の進捗", color=0xB9C42F)
                        embed.set_author(name=user.name, icon_url=user.avatar.url)
                        embed.add_field(
                            name="", value="\n".join([f"1. {p}" for p in progress])
                        )
                        text = f"<@{user_id}>"

                        cursor.execute(
                            "SELECT channel FROM channels WHERE user_id = %s",
                            (user_id,),
                        )
                        channels = [c[0] for c in cursor.fetchall()]
                        logger.debug(
                            f"[cron] Found {len(channels)} channel(s) for user {user_id}"
                        )

                        for channel_id in channels:
                            try:
                                channel = client.get_channel(channel_id)
                                if channel is None:
                                    logger.warning(
                                        f"[cron] Channel {channel_id} not found for user {user_id}"
                                    )
                                    continue
                                msg = await send_channel_message(
                                    user, channel, channel_id, text, embed, conn, cursor
                                )
                                logger.info(
                                    f"[cron] Progress sent to user {user_id} channel {channel_id}"
                                )
                            except Exception as e:
                                logger.exception(
                                    f"[cron] Error sending message to channel {channel_id} for user {user_id}: {e}"
                                )

                        try:
                            cursor.execute(
                                "SELECT message, timestamp FROM progress WHERE user_id = %s",
                                (user_id,),
                            )
                            rows = cursor.fetchall()
                            for message, timestamp in rows:
                                cursor.execute(
                                    "INSERT INTO backup_progress (user_id, message, timestamp) VALUES (%s, %s, %s)",
                                    (user_id, message, timestamp),
                                )
                            cursor.execute(
                                "DELETE FROM progress WHERE user_id = %s", (user_id,)
                            )
                            conn.commit()
                            logger.debug(
                                f"[cron] Progress entries backed up and cleared for user {user_id}"
                            )
                        except Exception as e:
                            logger.exception(
                                f"[cron] Backup or cleanup error for user {user_id}: {e}"
                            )
                            conn.rollback()

                        try:
                            await msg.add_reaction("👍")
                            await msg.add_reaction("👎")
                            await asyncio.sleep(86400)

                            msg = await msg.channel.fetch_message(msg.id)
                            consent = utils.get(msg.reactions, emoji="👍").count - 1
                            refusal = utils.get(msg.reactions, emoji="👎").count - 1
                            cursor.execute(
                                "INSERT INTO votes (user_id, message_id, consent, refusal) VALUES (%s, %s, %s, %s)",
                                (user_id, msg.id, consent, refusal),
                            )
                            conn.commit()
                            logger.info(f"[cron] Vote recorded for user {user_id}")
                        except Exception as e:
                            logger.exception(
                                f"[cron] Voting reaction or recording failed for user {user_id}: {e}"
                            )
                            conn.rollback()

                    except Exception as e:
                        logger.exception(
                            f"[cron] Error sending progress for user {user_id}: {e}"
                        )

                await asyncio.gather(*(send_progress(uid) for uid in user_ids))

            except Exception as e:
                logger.error(
                    "[cron] An error occurred during the overall progress sending process."
                )
                logger.exception(e)
                conn.rollback()

        async def notice(user_id, notice_time):
            try:
                if notice_time and now == notice_time:
                    if not aggr_internal(user_id, cursor):
                        user = await client.fetch_user(user_id)
                        logger.debug(f"[cron] Sending notice to user {user_id}")

                        embed = Embed(
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
                            "SELECT channel FROM channels WHERE user_id = %s",
                            (user_id,),
                        )
                        channels = [c[0] for c in cursor.fetchall()]
                        for channel_id in channels:
                            try:
                                channel = client.get_channel(channel_id)
                                if channel is None:
                                    logger.warning(
                                        f"[cron] Channel {channel_id} not found for notice to user {user_id}"
                                    )
                                    continue
                                await send_channel_message(
                                    user, channel, channel_id, text, embed, conn, cursor
                                )
                                logger.info(
                                    f"[cron] Notice sent to user {user_id} channel {channel_id}"
                                )
                            except Exception as e:
                                logger.exception(
                                    f"[cron] Error sending notice to channel {channel_id} for user {user_id}: {e}"
                                )

            except Exception as e:
                logger.exception(f"[cron] Error sending notice for user {user_id}: {e}")

        try:
            cursor.execute("SELECT user_id, notice FROM users")
            users = cursor.fetchall()
            logger.info(f"[cron] Fetched {len(users)} users for notice check")
            await asyncio.gather(*(notice(u[0], u[1]) for u in users))
        except Exception as e:
            logger.exception(f"[cron] Error during notice handling: {e}")
            conn.rollback()

    return cron
