# -*- coding: utf-8 -*-
from pydantic import BaseModel


class Config(BaseModel):
    # 模型配置
    gemini_api_key: str = ""
    base_url: str = ""
    model: str = ""

    # sqlite 配置
    database_file_path: str = ""