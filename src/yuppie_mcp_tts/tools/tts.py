"""TTS MCP 工具 — 文字转语音、列出嗓音、保存文件"""

from __future__ import annotations

import base64
import os

import edge_tts
from pydantic import BaseModel, ConfigDict, Field

DEFAULT_VOICE = "en-US-JennyNeural"

AVAILABLE_VOICES = [
    "en-US-JennyNeural",
    "en-US-GuyNeural",
    "en-US-AriaNeural",
    "en-US-DavisNeural",
    "en-US-JaneNeural",
    "en-US-JasonNeural",
    "en-US-NancyNeural",
    "en-US-SaraNeural",
    "en-US-TonyNeural",
    "en-GB-SoniaNeural",
    "en-GB-RyanNeural",
    "en-GB-LibbyNeural",
    "en-GB-MaisieNeural",
    "en-AU-NatashaNeural",
    "en-AU-WilliamNeural",
    "en-CA-ClaraNeural",
    "en-CA-LiamNeural",
    "en-IN-NeerjaNeural",
    "en-IN-PrabhatNeural",
    "en-IE-EmilyNeural",
    "en-IE-ConnorNeural",
    "en-SG-LunaNeural",
    "en-SG-WayneNeural",
    "en-ZA-LukeNeural",
    "en-ZA-SamNeural",
    "en-KE-AsiliaNeural",
    "en-KE-ChilembaNeural",
    "en-NG-EzinneNeural",
    "en-NG-AbeoNeural",
    "en-TZ-ImaniNeural",
    "en-TZ-ElimuNeural",
    "en-PH-RosaNeural",
    "en-PH-JamesNeural",
    "zh-CN-XiaoxiaoNeural",
    "zh-CN-YunxiNeural",
    "zh-CN-YunjianNeural",
    "zh-CN-XiaoyiNeural",
    "zh-CN-YunyangNeural",
    "fr-FR-DeniseNeural",
    "fr-FR-HenriNeural",
    "fr-FR-EloiseNeural",
    "de-DE-KatjaNeural",
    "de-DE-ConradNeural",
    "de-DE-AmalaNeural",
    "de-DE-BerndNeural",
    "ja-JP-NanamiNeural",
    "ja-JP-KeitaNeural",
    "ko-KR-SunHiNeural",
    "ko-KR-InJoonNeural",
    "pt-BR-FranciscaNeural",
    "pt-BR-AntonioNeural",
    "es-ES-AlvaroNeural",
    "es-ES-ElviraNeural",
    "es-MX-JorgeNeural",
    "es-MX-DaliaNeural",
]


class TTSInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    text: str = Field(..., min_length=1, description="要转换为语音的文本")
    voice: str = Field(default=DEFAULT_VOICE, description="嗓音名称")
    speed: float = Field(default=1.0, ge=0.1, le=3.0, description="语速倍率 (0.1~3.0)")


class TTSFileInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    text: str = Field(..., min_length=1, description="要转换为语音的文本")
    output_path: str = Field(..., min_length=1, description="MP3 文件保存路径（绝对路径）")
    voice: str = Field(default=DEFAULT_VOICE, description="嗓音名称")
    speed: float = Field(default=1.0, ge=0.1, le=3.0, description="语速倍率 (0.1~3.0)")


def _rate_str(speed: float) -> str:
    """将语速倍率转换为 edge-tts 的 rate 参数格式，如 +50%, -30%"""
    diff = int(round((speed - 1.0) * 100))
    if diff >= 0:
        return f"+{diff}%"
    return f"{diff}%"


def list_voices() -> str:
    """列出所有可用的 TTS 嗓音"""
    voices_info = "\n".join(f"  {i + 1}. {v}" for i, v in enumerate(AVAILABLE_VOICES))
    return (
        f"✅ 可用嗓音（共 {len(AVAILABLE_VOICES)} 个）\n\n"
        f"{voices_info}\n\n"
        "💡 使用 `text_to_speech` 或 `text_to_speech_file` 工具时通过 voice 参数指定嗓音。"
    )


async def text_to_speech(args: TTSInput) -> str:
    """文字转语音，返回 base64 编码的 MP3 音频"""
    try:
        communicate = edge_tts.Communicate(
            text=args.text, voice=args.voice, rate=_rate_str(args.speed)
        )
        audio_chunks: list[bytes] = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
        audio_bytes = b"".join(audio_chunks)
        b64 = base64.b64encode(audio_bytes).decode("utf-8")

        return (
            f"✅ 音频生成成功（{len(audio_bytes)} 字节，MP3）\n\n"
            f"嗓音: {args.voice}\n"
            f"语速: {args.speed}x\n"
            f"字符数: {len(args.text)}\n\n"
            f"Base64 编码:\n{b64}"
        )
    except Exception as e:
        return f"❌ 语音合成失败：{e}"


async def text_to_speech_file(args: TTSFileInput) -> str:
    """文字转语音并保存到文件"""
    try:
        communicate = edge_tts.Communicate(
            text=args.text, voice=args.voice, rate=_rate_str(args.speed)
        )
        audio_chunks: list[bytes] = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
        audio_bytes = b"".join(audio_chunks)

        abs_path = os.path.abspath(args.output_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "wb") as f:
            f.write(audio_bytes)

        return (
            f"✅ 音频已保存\n\n"
            f"路径: `{abs_path}`\n"
            f"大小: {len(audio_bytes):,} 字节\n"
            f"嗓音: {args.voice}\n"
            f"语速: {args.speed}x\n"
            f"字符数: {len(args.text)}"
        )
    except Exception as e:
        return f"❌ 语音合成失败：{e}"
