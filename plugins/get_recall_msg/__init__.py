# -*- coding: utf-8 -*-
from typing import Optional

from nonebot import on_notice, on_command, get_driver, logger
from nonebot.params import CommandArg
from nonebot.adapters import Bot, Event, Message
from aiosqlite import connect, Connection


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


sign_recall_msg = on_notice(
    priority=2,
    block=False
)


@sign_recall_msg.handle()
async def get_msg(bot: Bot, event: Event):
    msg_id = event.message_id
    user_id = event.user_id
    group_id = event.group_id
    logger.info(f"[msgRecall]群{group_id}的用户{user_id}撤回一条消息, msgId: {msg_id}")

    sql = f"UPDATE '{group_id}' SET isRecall = 'true' WHERE msgId = ?"
    await db_client.execute(sql, (msg_id,))
    await db_client.commit()

    await sign_recall_msg.finish()


async def check_message_type(event: Event) -> bool:
    if event.message_type == "group":
        return True
    else:
        return False


get_recall_msg = on_command(
    'recallMsg',
    rule=check_message_type,
    priority=4,
    force_whitespace=True,
    block=False
)


@get_recall_msg.handle()
async def get_recall_msg(bot: Bot, event: Event, message: Message = CommandArg()):
    group_id = event.group_id

    arg = message.extract_plain_text().strip()
    if not arg.startswith("user_id") or "=" not in arg:
        await bot.call_api("send_group_msg", group_id=group_id, message="[Ice] Params error.")

    select_user_id = arg.split("=")[-1]
    sql = f"SELECT userId, nicknameInGroup, msg, msgType FROM '{group_id}' WHERE userId = ? AND isRecall = 'true' ORDER BY timestamp DESC LIMIT 1;"
    async with db_client.execute(sql, (select_user_id,)) as result:
        row = await result.fetchone()
        if row is None:
            await bot.call_api("send_group_msg", group_id=group_id, message="[Ice] Result is none.")
        else:
            user_id = row[0]
            nickname_in_group = row[1]
            recall_msg = row[2]
            recall_msg_type = row[3]
            if recall_msg_type == "text":
                send_msg = [{
                    "type": "node",
                    "data": {
                        "user_id": user_id,
                        "nickname": nickname_in_group,
                        "content": [{
                            "type": "text",
                            "data": {
                                "text": recall_msg
                            }
                        }
                        ]
                    }
                }]
            elif recall_msg_type == "image":
                send_msg = [{
                    "type": "node",
                    "data": {
                        "user_id": user_id,
                        "nickname": nickname_in_group,
                        "content": [{
                            "type": "image",
                            "data": {
                                "file": recall_msg
                            }
                        }]
                    }
                }]

            await bot.call_api("send_group_forward_msg", group_id=group_id, message=send_msg)

    await sign_recall_msg.finish()