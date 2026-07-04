"""TTS 工具层 BaseModel 输入校验 + 工具逻辑测试"""

import pytest
from pydantic import ValidationError

from yuppie_mcp_tts.tools.tts import (
    DEFAULT_VOICE,
    AVAILABLE_VOICES,
    TTSInput,
    TTSFileInput,
    list_voices,
    _rate_str,
)


# ── _rate_str ──


@pytest.mark.parametrize(
    ("speed", "expected"),
    [
        (1.0, "+0%"),
        (1.5, "+50%"),
        (2.0, "+100%"),
        (0.5, "-50%"),
        (0.8, "-20%"),
    ],
)
def test_rate_str(speed: float, expected: str):
    assert _rate_str(speed) == expected


# ── TTSInput ──


def test_tts_input_required():
    with pytest.raises(ValidationError):
        TTSInput()


def test_tts_input_accepts_valid():
    args = TTSInput(text="Hello")
    assert args.text == "Hello"
    assert args.voice == DEFAULT_VOICE
    assert args.speed == 1.0


def test_tts_input_strips_whitespace():
    args = TTSInput(text="  Hello  ")
    assert args.text == "Hello"


def test_tts_input_forbids_extra():
    with pytest.raises(ValidationError):
        TTSInput(text="Hello", extra_field="bad")


def test_tts_input_custom_voice():
    args = TTSInput(text="Hello", voice="zh-CN-XiaoxiaoNeural")
    assert args.voice == "zh-CN-XiaoxiaoNeural"


def test_tts_input_custom_speed():
    args = TTSInput(text="Hello", speed=1.5)
    assert args.speed == 1.5


def test_tts_input_rejects_invalid_speed():
    with pytest.raises(ValidationError):
        TTSInput(text="Hello", speed=0.0)
    with pytest.raises(ValidationError):
        TTSInput(text="Hello", speed=5.0)


def test_tts_input_rejects_empty_text():
    with pytest.raises(ValidationError):
        TTSInput(text="")


# ── TTSFileInput ──


def test_tts_file_input_required():
    with pytest.raises(ValidationError):
        TTSFileInput()


def test_tts_file_input_accepts_valid():
    args = TTSFileInput(text="Hello", output_path="/tmp/test.mp3")
    assert args.text == "Hello"
    assert args.output_path == "/tmp/test.mp3"
    assert args.voice == DEFAULT_VOICE
    assert args.speed == 1.0


def test_tts_file_input_forbids_extra():
    with pytest.raises(ValidationError):
        TTSFileInput(text="Hello", output_path="/tmp/test.mp3", extra_field="bad")


def test_tts_file_input_rejects_empty_output_path():
    with pytest.raises(ValidationError):
        TTSFileInput(text="Hello", output_path="")


# ── list_voices ──


def test_list_voices_returns_all_voices():
    result = list_voices()
    assert "可用嗓音" in result
    assert f"共 {len(AVAILABLE_VOICES)} 个" in result
    assert DEFAULT_VOICE in result
    assert "zh-CN-XiaoxiaoNeural" in result


def test_list_voices_ordered():
    result = list_voices()
    lines = result.strip().split("\n")
    voice_lines = [l for l in lines if l.strip().startswith(("1.", "2.", "3."))]
    assert len(voice_lines) == min(3, len(AVAILABLE_VOICES))


# ── model_config ──


def test_tts_inputs_forbid_extra():
    args_list: list = [
        TTSInput(text="Hello"),
        TTSFileInput(text="Hello", output_path="/tmp/test.mp3"),
    ]
    for args in args_list:
        assert args.model_config.get("extra") == "forbid"
