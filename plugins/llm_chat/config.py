# -*- coding: utf-8 -*-
from pydantic import BaseModel


class Config(BaseModel):
    # 模型配置
    api_key: str = ""
    base_url: str = ""
    model: str = ""

    # MCP服务配置项
    mcp_servers: str = ""