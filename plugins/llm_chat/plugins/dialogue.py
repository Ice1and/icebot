# -*- coding: utf-8 -*-
from re import findall
from json import load, loads, dumps
from typing import Optional, List, Union
from contextlib import AsyncExitStack

from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from nonebot import on_command, get_driver, get_plugin_config, logger
from nonebot.drivers import Driver
from nonebot.adapters import Event, Bot, Message
from nonebot.params import CommandArg

from ..config import Config


plugin_config = get_plugin_config(Config)


class ChatBot:
    def __init__(self) -> None:
        self.exit_stack = AsyncExitStack()
        self.available_tools = []
        self.available_prompts = []
        self.sessions = {}
        self.config = plugin_config
        self.client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )


    async def connect_mcp_server(self, name: str, connect_type: str, command: Optional[str], args: Union[List[str], str]) -> None:
        if connect_type == "cmd":
            server_params = StdioServerParameters(
                command=command,
                args=args,
                env=None
            )
            read, write = await self.exit_stack.enter_async_context(stdio_client(server_params))
        else:
            read, write = await self.exit_stack.enter_async_context(sse_client(args))

        session = await self.exit_stack.enter_async_context(ClientSession(read, write))
        await session.initialize()

        # load tools and prompts
        response = await session.list_tools()
        if response.tools:
            for tool in response.tools:
                logger.success(f"[llm_chat] + tool {tool.name}")
                self.sessions[tool.name] = session
                self.available_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": {
                            k: v for k, v in tool.inputSchema.items() if k != "$schema"
                        }
                    }
                })


    async def connect_mcp_servers(self) -> None:
        with open(self.config.mcp_servers) as f:
            mcp_servers = load(f)
            for k, v in mcp_servers["mcpServers"].items():
                await self.connect_mcp_server(
                    name=k,
                    connect_type=v["type"],
                    command=v["command"],
                    args=v["args"]
                )


    async def cleanup(self) -> None:
        await self.exit_stack.aclose()


    async def process_dialog(self, bot: Bot, event: Event, message: str) -> None:
        prompt = """
            - 你是一个大学教授的助理，可以帮助提问的用户解决问题，需要严谨考虑回答用户的信息
            - 你不能回复自己是一个LLM或大语言模型
            - 当你有不知道的事情或无法解决的问题时，请使用`bing_search`这个工具
            - 你不能使用`fetch_webpage`这个工具，这一点很重要，请严格遵守
            - 你可以使用以下的工具:
                1. bing_search: 用于搜索互联网上的实时数据
        """
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": message}
        ]

        while True:
            is_use_tool = False

            llm_resp = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                tools=self.available_tools,
                timeout=10.0
            )

            llm_reply = llm_resp.choices[0].message
            logger.info(f"\nllm_reply: {llm_reply}")

            if getattr(llm_reply, "tool_calls"):
                is_use_tool = True
                messages.append(llm_reply)

                # call tool
                tool_name = llm_reply.tool_calls[0].function.name
                tool_args = llm_reply.tool_calls[0].function.arguments

                send_msg = f"[Ice] Accomplish this matter using the `{tool_name}` tool"
                await bot.call_api("send_group_msg", group_id=event.group_id, message=send_msg)

                session = self.sessions[tool_name]
                tool_result = await session.call_tool(tool_name, loads(tool_args))

                messages.append({
                    "role": "tool",
                    "tool_call_id": llm_reply.tool_calls[0].id,
                    "content": dumps(tool_result.content[0].text, ensure_ascii=False)
                })

            if not is_use_tool:
                send_msg = llm_reply.content.strip()
                await bot.call_api("send_group_msg", group_id=event.group_id, message=send_msg)
                break


driver: Driver = get_driver()
chatbot: Optional[ChatBot] = None


@driver.on_startup
async def _() -> None:
    global chatbot
    chatbot = ChatBot()

    logger.info("[llm_chat] 初始化MCP服务")
    await chatbot.connect_mcp_servers()


@driver.on_shutdown
async def _() -> None:
    global chatbot
    await chatbot.cleanup()


async def check_message_type(event: Event) -> bool:
    if event.message_type == "group":
        return True
    else:
        return False


llm_chat_responder = on_command(
    "llm",
    rule=check_message_type,
    priority=6,
    force_whitespace=True,
    block=False
)


@llm_chat_responder.handle()
async def llm_chat(bot: Bot, event: Event, message: Message = CommandArg()) -> None:
    global chatbot
    user_speech = message.extract_plain_text().strip()
    await chatbot.process_dialog(bot=bot, event=event, message=user_speech)

    await llm_chat_responder.finish()
