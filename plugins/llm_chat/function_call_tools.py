# -*- coding: utf-8 -*-
from parsel import Selector
from aiohttp import ClientSession


get_weather_tool = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "获取用户给定位置的实时天气,当用户询问“天气”、“温度”、“气温”、“湿度”等相关问题时，请使用此函数。",
        "parameters": {
            "type": "object",   # 模型返回的参数格式
            "properties": {
                "location": {
                    "type": "string",
                    "description": "城市名称，如北京、上海、纽约、伦敦"
                }
            },
            "required": ["location"],
        }
    }
}

tools = [get_weather_tool]


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
}


async def get_location_link(location: str) -> str:
    url = "https://geoapi.qweather.com/v2/city/lookup"
    parameters = {
        "key": "bdd98ec1d87747f3a2e8b1741a5af796",
        "location": location,
        "lang": "zh"
    }
    async with ClientSession() as session:
        async with session.get(
                url=url,
                headers=headers,
                params=parameters
        ) as resp:
            resp = await resp.json()
            return resp["location"][0]["fxLink"]


async def get_weather(location: str) -> str:
    location_link = await get_location_link(location)
    async with ClientSession() as session:
        async with session.get(
            url=location_link,
            headers=headers,
        ) as resp:
            sel = Selector(text=await resp.text())
            return sel.xpath("//div[@class='current-abstract']/text()").get().replace("\n", "")


functions = {
    "get_weather": get_weather,
}
