# -*- coding: utf-8 -*-
from pydantic import BaseModel, field_validator


class Config(BaseModel):
    # 模型配置
    gemini_api_key: str = "AIzaSyDXcmRCPoLxBLqh4ybbM1EWQP5TbyukiMs"
    base_url: str = "https://ice1and-openai-gemi.deno.dev/v1"
    model: str = "gemini-2.0-flash"

    # sqlite 配置
    database_file_path: str = "db/llm_chat.db"