# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## 项目概述

`yuppie-mcp-tts` 是一个 MCP (Model Context Protocol) Server，基于 [edge-tts](https://github.com/rany2/edge-tts)（微软 Edge 免费 TTS 引擎）提供文字转语音能力。无需 API Key。

## 开发命令

```bash
# 安装开发依赖
uv pip install -e ".[dev]"

# 运行测试
uv run pytest -v

# 代码检查
ruff check src/
ruff format --check src/

# 类型检查
mypy src/

# 本地运行 MCP Server（stdio 模式）
uv run yuppie-mcp-tts
```

## 架构设计

### 核心模块

- **`server.py`**: MCP Server 入口，MCPServer 注册所有工具
- **`tools/tts.py`**: TTS 工具实现
  - Pydantic `BaseModel`（`str_strip_whitespace` + `extra="forbid"`）+ `async def` 实现 + markdown 输出 + try/except 友好错误
  - edge-tts 原生异步，无需 `asyncio.to_thread()`

### 传输模式

默认 stdio（MCP 主流用法）。`main()` 根据 `MCP_TRANSPORT` 环境变量切换：`streamable-http` 时通过 `run()` 的 `host`/`port` 参数启动（默认 `127.0.0.1:8000`）。

## 代码规范

- 使用 `ruff`（line-length = 100）和 `mypy`（strict = true）
- 异步函数 `async def`
- 所有工具参数通过 Pydantic BaseModel 校验
- 工具返回 markdown 字符串；失败时返回 `❌ ...失败：{异常}`

## API 参考

- `text_to_speech(text, voice, speed)` — 文字转语音返回 base64 MP3
- `list_voices()` — 列出所有可用嗓音（50+）
- `text_to_speech_file(text, output_path, voice, speed)` — 文字转语音保存到文件
