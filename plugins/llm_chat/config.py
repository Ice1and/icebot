# -*- coding: utf-8 -*-
from os.path import dirname, join, abspath
from pydantic import BaseModel


class DataBaseConfig(BaseModel):
    database_file_path: str = "db/llm_chat.db"

class McpServerConfig(BaseModel):
    mcp_servers: str = join(dirname(abspath(__file__)), "mcp-servers.json")

class Config(BaseModel):
    # 模型配置
    api_key: str = "AIzaSyDXcmRCPoLxBLqh4ybbM1EWQP5TbyukiMs"
    base_url: str = "https://ice-openai-gemini-pqqnp5fmhyna.deno.dev/v1"
    model: str = "models/gemini-2.5-flash-preview-04-17"

    # 数据库配置项
    database_config: DataBaseConfig

    # MCP服务配置项
    mcp_server_config: McpServerConfig