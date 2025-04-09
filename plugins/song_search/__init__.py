# -*- coding: utf-8 -*-
import asyncio
from json import dumps, loads
from typing import Dict, Union

import aiohttp
from nonebot import on_command
from nonebot.adapters import Bot, Message, Event
from nonebot.params import CommandArg

from .encrypt import get_encrypt_data



async def check_message_type(event: Event) -> bool:
    if event.message_type == "group":
        return True
    else:
        return False


choose_song_responder = on_command(
    "点歌",
    rule=check_message_type,
    priority=10,
    force_whitespace=True,
    block=False,
)


@choose_song_responder.handle()
async def choose_song_func(bot: Bot, event: Event, message: Message = CommandArg()):
    """
    choose song
    :param bot:
    :param event:
    :param message:
    :return: songId: str
    """
    song_name = message.extract_plain_text()
    plaintext = {
        "s": song_name,
        "limit": 8,
        "csrf_token": "131db2e1e612612cf9401298e411c1f3"
    }
    cipher_data = get_encrypt_data(dumps(plaintext))

    loop = asyncio.get_running_loop()
    coro = search_song(cipher_data)
    song_id = await asyncio.ensure_future(coro, loop=loop)

    respond_msg = {
        "type": "music",
        "data": {
            "type": "163",
            "id": song_id
        }
    }
    if not song_id:
        respond_msg = "[IceBot] Song Search Failed"

    await bot.call_api("send_group_msg", group_id=event.group_id, message=respond_msg)
    await choose_song_responder.finish()


async def search_song(cipher_data: Dict) -> Union[str, None]:
    """

    :param cipher_data:
    :return: songId: int
    """
    request_url = "https://music.163.com/weapi/search/suggest/web?csrf_token=131db2e1e612612cf9401298e411c1f3"
    headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"}
    async with aiohttp.ClientSession(headers=headers) as async_session:
        async with async_session.post(url=request_url, data=cipher_data) as resp:
            resp = loads(await resp.text())
            try:
                return resp["result"]["songs"][0]["id"]
            except KeyError:
                return None