#-*- coding: utf-8 -*-
import nonebot
from nonebot import logger
from nonebot.adapters.onebot import V11Adapter


# nonebot 初始化
nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(V11Adapter)

# 加载插件
nonebot.load_from_toml("plugin_config.toml", encoding="utf-8")


if __name__ == '__main__':
    nonebot.run()