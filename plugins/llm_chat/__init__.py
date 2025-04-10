# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Union, List, Dict
from sqlite3 import Connection, connect

from openai import AsyncOpenAI, ChatCompletion
from nonebot import get_driver, get_plugin_config, on_message
from nonebot.adapters import Bot, Event
from nonebot.rule import to_me
from nonebot.plugin import PluginMetadata
from nonebot.log import logger

from .config import Config
from .database_tools import (
    query_recent_history_message,
    insert_messages_to_table
)


__plugin_meta__ = PluginMetadata(
    name="llm-chat",
    description="调用大模型API完成对话任务",
    usage="",
    config=Config
)


driver = get_driver()
plugin_config = get_plugin_config(Config)

sqlite_connect: Union[None, Connection] = None

gemini_client = AsyncOpenAI(
    api_key=plugin_config.gemini_api_key,
    base_url=plugin_config.base_url,
)


@driver.on_startup
async def open_sqlite_connect() -> None:
    global sqlite_connect
    sqlite_connect = connect(plugin_config.database_file_path)

@driver.on_shutdown
async def close_sqlite_connect() -> None:
    sqlite_connect.close()


llm_chat_responder = on_message(
    rule=to_me(),
    priority=2,
    block=False
)


async def get_completion(messages: List[Dict[str, str]]) -> ChatCompletion:
    completion = await gemini_client.chat.completions.create(
        model=plugin_config.model,
        temperature=0.4,
        messages=messages
    )
    return completion


@llm_chat_responder.handle()
async def llm_chat(bot: Bot, event: Event) -> None:
    # 封装用户消息
    user_message_json = {
        "role": "user",
        "content": event.get_message().extract_plain_text(),
        "timestamp": datetime.fromtimestamp(event.time).strftime('%Y-%m-%d %H:%M:%S'),
    }

    # 事件的消息类型为群聊
    if event.message_type == "group":
        group_id = event.group_id

        # 将用户消息合并至历史上下文中
        history_messages = query_recent_history_message(conn=sqlite_connect, table_name=group_id)
        history_messages.append(user_message_json)

        logger.debug(history_messages)

        # 获取大模型回复并返回给用户
        llm_reply = await get_completion(history_messages)
        llm_reply_message = llm_reply.choices[0].message.content.strip()
        await bot.call_api("send_group_msg", group_id=group_id, message=llm_reply_message)

        # 将用户消息和大模型回复消息一同存入数据库
        llm_reply_message_json = {
            "role": "assistant",
            "content": llm_reply_message,
            "timestamp": datetime.fromtimestamp(llm_reply.created).strftime('%Y-%m-%d %H:%M:%S'),
        }
        messages = [user_message_json, llm_reply_message_json]
        # logger.debug(messages)
        insert_messages_to_table(
            conn=sqlite_connect,
            table_name=group_id,
            messages=messages
        )

    # 私聊
    if event.message_type == "private":
        pass

    await llm_chat_responder.finish()