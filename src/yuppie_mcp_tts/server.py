"""TTS MCP Server 主入口 — 基于 edge-tts，无需 API Key"""

from __future__ import annotations

import os
from typing import Annotated, Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from . import __version__
from .tools import tts

mcp = FastMCP(
    "yuppie_mcp",
    instructions=(
        "TTS (文字转语音) MCP Server —— 基于 edge-tts (微软 Edge 免费 TTS 引擎)，"
        "无需 API Key。支持 50+ 嗓音、可调速、返回 base64 音频或保存到文件。"
    ),
)
mcp._mcp_server.version = __version__


@mcp.tool(
    name="text_to_speech",
    annotations=ToolAnnotations(
        title="文字转语音（返回 base64 音频）",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_text_to_speech(
    text: Annotated[str, "要转换为语音的文本"],
    voice: Annotated[
        Optional[str], "嗓音名称（使用 list_voices 查看可用嗓音）"
    ] = tts.DEFAULT_VOICE,
    speed: Annotated[Optional[float], "语速倍率 (0.1~3.0)，1.0 为正常"] = 1.0,
) -> str:
    """将文字转换为语音，返回 base64 编码的 MP3 音频。无需 API Key。"""
    return await tts.text_to_speech(tts.TTSInput(text=text, voice=voice, speed=speed))


@mcp.tool(
    name="list_voices",
    annotations=ToolAnnotations(
        title="列出 TTS 可用嗓音",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_list_voices() -> str:
    """列出所有可用的 TTS 嗓音（50+，覆盖中英文等多语种）。"""
    return tts.list_voices()


@mcp.tool(
    name="text_to_speech_file",
    annotations=ToolAnnotations(
        title="文字转语音并保存到文件",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_text_to_speech_file(
    text: Annotated[str, "要转换为语音的文本"],
    output_path: Annotated[str, "MP3 文件保存路径（绝对路径，如 /tmp/output.mp3）"],
    voice: Annotated[
        Optional[str], "嗓音名称（使用 list_voices 查看可用嗓音）"
    ] = tts.DEFAULT_VOICE,
    speed: Annotated[Optional[float], "语速倍率 (0.1~3.0)，1.0 为正常"] = 1.0,
) -> str:
    """将文字转换为语音并保存为 MP3 文件到磁盘。无需 API Key。"""
    return await tts.text_to_speech_file(
        tts.TTSFileInput(
            text=text, output_path=output_path, voice=voice, speed=speed
        )
    )


def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", "streamable-http")
    if transport == "streamable-http":
        mcp.settings.port = int(os.getenv("MCP_PORT", "8080"))
        mcp.run(transport="streamable-http")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
