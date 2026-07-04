# yuppie-mcp-tts

TTS (文字转语音) MCP Server — 基于 [edge-tts](https://github.com/rany2/edge-tts) (微软 Edge 免费 TTS 引擎)，无需 API Key，无需配置。

## 功能

| 工具名 | 说明 |
|--------|------|
| `text_to_speech` | 文字转语音，返回 base64 MP3 音频（可选嗓音、语速） |
| `list_voices` | 列出 50+ 可用嗓音（中英文等多语种） |
| `text_to_speech_file` | 文字转语音并保存为 MP3 文件到磁盘 |

**参数说明：**
- `voice`: 嗓音名称，如 `en-US-JennyNeural`、`zh-CN-XiaoxiaoNeural`，默认 `en-US-JennyNeural`
- `speed`: 语速倍率 0.1~3.0，1.0 为正常速度

## 快速开始

### 安装

```bash
pip install yuppie-mcp-tts
```

### 运行

```bash
yuppie-mcp-tts
```

无需任何配置，开箱即用。

## MCP 集成

### Claude Code

在 `.mcp.json` 中添加：

```json
{
  "mcpServers": {
    "yuppie-mcp-tts": {
      "type": "stdio",
      "command": "uvx",
      "args": ["--refresh", "yuppie-mcp-tts"]
    }
  }
}
```

### Cursor / Cherry Studio / Claude Desktop / OpenCode

```json
{
  "mcpServers": {
    "yuppie-mcp-tts": {
      "command": "uvx",
      "args": ["--refresh", "yuppie-mcp-tts"]
    }
  }
}
```

## 可用嗓音

50+ 嗓音覆盖多种语言和地区变体：

**英语 (US):** JennyNeural, GuyNeural, AriaNeural, DavisNeural, JaneNeural, JasonNeural, NancyNeural, SaraNeural, TonyNeural

**英语 (UK):** SoniaNeural, RyanNeural, LibbyNeural, MaisieNeural

**英语 (AU):** NatashaNeural, WilliamNeural

**英语 (CA):** ClaraNeural, LiamNeural

**英语 (IN):** NeerjaNeural, PrabhatNeural

**中文:** XiaoxiaoNeural, YunxiNeural, YunjianNeural, XiaoyiNeural, YunyangNeural

**其他:** 法语、德语、日语、韩语、葡萄牙语、西班牙语等

使用 `list_voices` 工具可查看完整列表。

## 示例

```text
用户: 把 "你好世界" 转成语音
AI: [调用 text_to_speech(text="你好世界", voice="zh-CN-XiaoxiaoNeural")]

用户: 把 "Hello World" 用英式发音保存到 /tmp/hello.mp3
AI: [调用 text_to_speech_file(text="Hello World", voice="en-GB-SoniaNeural", output_path="/tmp/hello.mp3")]
```

## 开发

```bash
uv pip install -e ".[dev]"
uv run pytest -v
```

### 本地调试

```bash
npx @modelcontextprotocol/inspector uv run yuppie-mcp-tts
```

## 许可证

MIT
