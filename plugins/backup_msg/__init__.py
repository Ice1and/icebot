# -*- coding: utf-8 -*-
from typing import Optional
from datetime import datetime

from aiosqlite import connect, Connection
from nonebot import on_message, get_driver
from nonebot.adapters import Bot, Event


database_path = "db/backup_msg.db"
driver = get_driver()
db_client: Optional[Connection] = None


@driver.on_startup
async def connect_db():
    global db_client
    db_client = await connect(database_path)


@driver.on_shutdown
async def close_db():
    global db_client
    await db_client.close()


async def message_type(event: Event) -> bool:
    if event.message_type == "group":
        return True
    else:
        return False


backup_msg_responder = on_message(
    rule=message_type,
    priority=1,
    block=False
)


@backup_msg_responder.handle()
async def backup_msg(bot: Bot, event: Event):
    """消息自动备份

    """
    # print(event)
    group_id = event.group_id
    message_id = event.message_id
    user_id = event.user_id
    nickname_in_group = event.sender.card
    if not nickname_in_group:
        nickname_in_group = event.sender.nickname
    sender_timestamp = datetime.fromtimestamp(event.time).strftime("%Y-%m-%d %H:%M:%S")
    msg = None
    msg_type = None

    sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
    async with db_client.execute(sql, (group_id,)) as result:
        if await result.fetchone() is None:
            # 建表
            await db_client.execute(f"""
                        CREATE TABLE '{group_id}'(
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            userId CHAR(35),
                            nicknameInGroup CHAR(35),
                            msgId CHAR(35),
                            msgType CHAR(10),
                            msg LONGTEXT,
                            isRecall CHAR(10) DEFAULT 'false',
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
            await db_client.commit()

    for seg in event.get_message():
        msg_type = seg.type

        if msg_type == "image":
            file = seg.data["file"]
            msg = (await bot.call_api("get_image", file=file))["url"]

        elif msg_type == "text":
            msg = seg.data["text"]

        elif msg_type == "video":
            pass

        elif msg_type == "face":
            pass

        elif msg_type == "forward":
            pass

    if msg:
        sql = f"INSERT INTO '{group_id}' (userId, nicknameInGroup, msgId, msgType, msg, timestamp) VALUES (?, ?, ?, ?, ?, ?)"
        await db_client.execute(sql, (user_id, nickname_in_group, message_id, msg_type, msg, sender_timestamp))
        await db_client.commit()

    await backup_msg_responder.finish()