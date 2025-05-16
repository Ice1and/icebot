# -*- coding: utf-8 -*-
from re import findall
from datetime import datetime
from time import time
from typing import Optional

from aiohttp import ClientSession
from nonebot import on_command, get_driver
from nonebot.adapters import Bot, Event


async def check_message_type(event: Event) -> bool:
    if event.message_type == "group":
        return True
    else:
        return False


bot_driver = get_driver()
session: Optional[ClientSession] = None


@bot_driver.on_startup
async def _():
    global session
    session = ClientSession()


@bot_driver.on_shutdown
async def _():
    global session
    await session.close()


gold_price_responder = on_command(
    "goldPrice",
    rule=check_message_type,
    priority=4,
    force_whitespace=True,
    block=False,
)

@gold_price_responder.handle()
async def query_gold_price(bot: Bot, event: Event):
    url = "http://www.huangjinjiage.cn/jin.js"
    time_stamp = int(time() * 1000)
    params = {
        "t": time_stamp,
    }
    headers = {
        "Content-Type": "application/x-javascript"
    }
    async with session.get(url, headers=headers, params=params) as resp:
        results = findall('var hq_str_gds_AUTD="(.*?),黄金延期";', await resp.text(encoding="gbk"))[0].split(",")
        gold_price = f"""
🪙国内金价🪙:
    最新价格: {results[0]},
    开盘价格: {results[8]},
    昨收盘价: {results[7]},
    今日最高: {results[4]},
    今日最低: {results[5]},
    {datetime.fromtimestamp(time_stamp / 1000).strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        await bot.call_api("send_msg", message_type="group", group_id=event.group_id, message=gold_price)
        await gold_price_responder.finish()