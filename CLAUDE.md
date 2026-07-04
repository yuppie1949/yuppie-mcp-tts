# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

## 项目概述

`yuppie-mcp-fnf` 是一个 MCP (Model Context Protocol) Server，让 AI 助手通过 MCP 协议操作阿里云 FNF（Serverless 工作流）。基于阿里云 FNF OpenAPI SDK，覆盖流程管理和执行管理两大业务域。

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
FNF_ACCESS_KEY_ID=xxx FNF_ACCESS_KEY_SECRET=xxx uv run yuppie-mcp-fnf
```

## 架构设计

### 核心模块

- **`server.py`**: MCP Server 入口，FastMCP 注册工具
- **`utils/config.py`**: `FNFConfig` 数据类，`from_env()` 读取并校验 `FNF_ACCESS_KEY_ID`/`FNF_ACCESS_KEY_SECRET`/`FNF_ENDPOINT`，自动加载 `.env`。支持阿里云标准环境变量（`ALIBABA_CLOUD_ACCESS_KEY_ID`）和项目专用变量，项目专用优先。
- **`utils/fnf/`**: FNF 客户端
  - `client.py` — `AliyunFNFClient`：封装 `alibabacloud_fnf20190315` SDK，提供同步方法。包括 `describe_flow`、`list_flows`、`start_execution`、`start_sync_execution`、`stop_execution`、`describe_execution`、`list_executions`、`get_execution_history`
- **`tools/`**: MCP 工具层
  - `flows.py` — 流程管理工具
  - `executions.py` — 执行管理工具
  - 每个工具：Pydantic `BaseModel`（`str_strip_whitespace` + `extra="forbid"`）+ `async def` 实现 + markdown 输出 + try/except 友好错误
  - 由于 SDK 是同步的，使用 `asyncio.to_thread()` 异步包装

### 客户端懒加载

`_get_client()` 首次调用时从环境变量读取配置并构造 `AliyunFNFClient`，后续重用。两个 tools 模块各自独立懒加载。

### 传输模式

仅支持 stdio（MCP 主流用法）。`server.py` 直接 `mcp.run()`。

## 代码规范

- 使用 `ruff`（line-length = 100）和 `mypy`（strict = true）
- 异步函数 `async def`，同步 SDK 调用用 `asyncio.to_thread` 包装
- 所有工具参数通过 Pydantic BaseModel 校验
- 工具返回 markdown 字符串；失败时返回 `❌ ...失败：{异常}`
- FNF 客户端返回统一格式 `{"success": bool, "data": dict, "error": dict}`

## API 参考

### 流程管理
- `fnf_describe_flow(name)` — 获取流程详细信息
- `fnf_describe_flow_inputs(name)` — 获取流程信息及入参定义（含类型、示例 JSON）
- `fnf_list_flows(limit, next_token)` — 批量查询流程列表（支持分页）

### 执行管理
- `fnf_start_execution(flow_name, execution_name, input_data)` — 异步启动执行
- `fnf_start_sync_execution(flow_name, execution_name, input_data)` — 同步启动执行
- `fnf_stop_execution(flow_name, execution_name, cause)` — 停止执行
- `fnf_describe_execution(flow_name, execution_name)` — 查询执行状态
- `fnf_list_executions(flow_name, limit, next_token)` — 查询执行历史列表（支持分页）
- `fnf_get_execution_history(flow_name, execution_name, limit, next_token)` — 获取执行步骤详情（支持分页）

## 入参定义（fnf_describe_flow_inputs）

`fnf_describe_flow_inputs` 可以从 Flow 的 States 中解析出入参定义（变量名 + 类型），
让 AI 知道每个参数应该填什么格式。

### 配置方式

在 FNF Flow 中创建一个 **模板转换** 节点（`Action: Extensions:TemplateTransform`），
放在"开始"节点之后，`template` 字段直接写入参的 JSON 定义：

```json
{
    "参数名": {
        "type": "string",        // 必填，支持的类型见下表
        "label": "显示名称",      // 可选，参数的展示名称
        "required": 1,           // 可选，1=必填，省略=选填
        "enum": ["选项A", "选项B"]  // select 类型必填，可选值列表
    }
}
```

### 支持的类型

| 类型 | 含义 | 示例值 |
|------|------|--------|
| `string` | 字符串 | `"示例文本"` |
| `int` | 整数 | `0` |
| `select` | 下拉选择（需 `enum`） | `"第一个选项"` |
| `object` | JSON 对象 | `{"key": "value"}` |
| `array[string]` | 字符串数组 | `["item1", "item2"]` |
| `file` | 单个文件 | `"https://example.com/file.pdf"` |
| `file-list` | 文件列表 | `["url1", "url2"]` |

### 完整示例

在模板转换节点的 template 字段粘贴：

```json
{
    "title": {"type": "string", "label": "文章标题", "required": 1},
    "partment": {"type": "select", "label": "部门", "enum": ["销售部", "技术部"]},
    "count": {"type": "int", "label": "数量"},
    "info": {"type": "object", "label": "详细信息"},
    "tags": {"type": "array[string]", "label": "标签"},
    "cover": {"type": "file", "label": "封面URL"},
    "attachments": {"type": "file-list", "label": "附件列表"}
}
```

### 兜底方案

如果 Flow 中没有模板转换节点，会尝试解析 **代码节点**（`Extensions:CodeExecutor`，
名称含"入参说明"）的 Parameters.code 字段（Python 代码的 return dict）。
建议优先使用模板转换节点，避免 JSON 转义问题。
