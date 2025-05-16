# -*- coding: utf-8 -*-
from os.path import dirname, abspath, join

from nonebot import load_plugins
from nonebot.plugin import PluginMetadata


__plugin_meta__ = PluginMetadata(
    name="LLM_Chat",
    description="支持LLM多轮对话、MCP协议",
    type="application",
    usage="/llm"
)

load_plugins(
    join(dirname(abspath(__file__)), "plugins")
)
