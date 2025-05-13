# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Union, List, Dict
from sqlite3 import Connection, connect
from json import loads, dumps
from copy import deepcopy

import asyncio
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from nonebot import get_driver, get_plugin_config, on_command
from nonebot.adapters import Bot, Event
from nonebot.rule import to_me
from nonebot.plugin import PluginMetadata
from nonebot.log import logger

from .config import Config
from .database_tools import (
    query_recent_history_message,
    insert_messages_to_table
)
from .function_call_tools import tools, get_weather, functions


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
    api_key=plugin_config.api_key,
    base_url=plugin_config.base_url,
)


@driver.on_startup
async def open_sqlite_connect() -> None:
    global sqlite_connect
    sqlite_connect = connect(plugin_config.database_file_path)

@driver.on_shutdown
async def close_sqlite_connect() -> None:
    sqlite_connect.close()


async def check_message_type(event: Event) -> bool:
    if event.message_type == "group":
        return True
    else:
        return False


llm_chat_responder = on_command(
    'llm',
    rule=check_message_type,
    priority=2,
    force_whitespace=True,
    block=False
)


async def get_completion(messages: List[Union[Dict[str, str], ChatCompletionMessage]]) -> ChatCompletion:
    for message in messages:
        if type(message) is dict:
            message.pop("timestamp", None)

    completion = await gemini_client.chat.completions.create(
        model=plugin_config.model,
        temperature=0.3,
        messages=messages,
        tools=tools,
        tool_choice="auto"
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
        history_messages.append(deepcopy(user_message_json))

        logger.debug(history_messages)

        # 获取大模型回复
        completion = await get_completion(history_messages)
        tool_calls_information = completion.choices[0].message.tool_calls
        # print("tool calls: ", end="")
        # print(tool_calls_information)
        if tool_calls_information:
            location = loads(tool_calls_information[0].function.arguments)["location"]
            function_name = tool_calls_information[0].function.name
            tool_call_id = tool_calls_information[0].id

            # 执行函数
            loop = asyncio.get_running_loop()
            coro = functions[function_name](location)
            result = await loop.create_task(coro)

            print("result: " + result.strip())
            history_messages.append(completion.choices[0].message)
            history_messages.append({
                "role": "tool",
                "tool_call_id": tool_call_id,
                "content": dumps(result.strip(), ensure_ascii=False)        # 需转换成JSON格式，否则报错
            })
            # print(history_messages)
            completion = await get_completion(history_messages)

        llm_reply_message = completion.choices[0].message.content.strip()
        await bot.call_api("send_group_msg", group_id=group_id, message=llm_reply_message)

        # 将用户消息和大模型回复消息一同存入数据库
        llm_reply_message_json = {
            "role": "assistant",
            "content": llm_reply_message,
            "timestamp": datetime.fromtimestamp(completion.created).strftime('%Y-%m-%d %H:%M:%S'),
        }
        messages = [user_message_json, llm_reply_message_json]
        logger.debug(messages)
        insert_messages_to_table(
            conn=sqlite_connect,
            table_name=group_id,
            messages=messages
        )

    # 私聊
    if event.message_type == "private":
        pass

    await llm_chat_responder.finish()