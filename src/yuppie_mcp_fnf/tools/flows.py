"""流程管理 MCP 工具 — 查询流程、批量列表"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from ..utils.config import FNFConfig
from ..utils.fnf import AliyunFNFClient

_client: AliyunFNFClient | None = None


def _get_client() -> AliyunFNFClient:
    global _client
    if _client is None:
        config = FNFConfig.from_env()
        _client = AliyunFNFClient(
            endpoint=config.endpoint,
            access_key_id=config.access_key_id,
            access_key_secret=config.access_key_secret,
        )
    return _client


class DescribeFlowInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(..., min_length=1, description="流程名称")


class ListFlowsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    limit: Optional[int] = Field(
        None, ge=1, le=1000, description="返回数量，取值范围 [1, 1000)，默认 60"
    )
    next_token: Optional[str] = Field(None, description="下一个查询令牌（分页使用）")


def _flow_to_md(flow: Dict[str, Any]) -> str:
    """单条流程格式化为 markdown 片段"""
    lines = [
        f"- **名称**: `{flow.get('Name', '')}`",
        f"  - **ID**: `{flow.get('Id', '')}`",
        f"  - **类型**: {flow.get('Type', '')}",
        f"  - **执行模式**: {flow.get('ExecutionMode', '')}",
        f"  - **描述**: {flow.get('Description', '-')}",
        f"  - **创建时间**: {flow.get('CreatedTime', '')}",
        f"  - **修改时间**: {flow.get('LastModifiedTime', '')}",
    ]
    if flow.get("RoleArn"):
        lines.append(f"  - **角色 ARN**: `{flow['RoleArn']}`")
    return "\n".join(lines)


async def describe_flow(args: DescribeFlowInput) -> str:
    """获取一个流程的详细信息"""
    try:
        client = _get_client()
        result = await asyncio.to_thread(client.describe_flow, args.name)
        if not result.get("success"):
            err = result.get("error", {})
            return f"❌ 查询流程失败：{err.get('Message', err)}"

        data = result["data"]
        return (
            f"✅ 流程信息\n\n"
            f"| 属性 | 值 |\n"
            f"|------|-----|\n"
            f"| 名称 | `{data.get('Name', '')}` |\n"
            f"| ID | `{data.get('Id', '')}` |\n"
            f"| 类型 | {data.get('Type', '')} |\n"
            f"| 执行模式 | {data.get('ExecutionMode', '')} |\n"
            f"| 描述 | {data.get('Description', '-')} |\n"
            f"| 创建时间 | {data.get('CreatedTime', '')} |\n"
            f"| 修改时间 | {data.get('LastModifiedTime', '')} |\n"
            f"| 角色 ARN | `{data.get('RoleArn', '-')}` |"
        )
    except Exception as e:
        return f"❌ 查询流程失败：{e}"


_EXAMPLE_VALUES: dict[str, Any] = {
    "string": "示例文本",
    "int": 0,
    "select": "选项A",
    "object": {"key": "value"},
    "array": ["item1", "item2"],
    "file": "https://example.com/file.pdf",
    "file-list": ["https://example.com/file1.pdf"],
}


def _resolve_type(param_type: str) -> str:
    """将可能的复合类型（如 array[string]）解析为基础类型名"""
    if "[" in param_type:
        return param_type.split("[")[0]
    return param_type


def _make_example_value(param: dict[str, Any]) -> Any:
    """根据参数类型生成示例值"""
    param_type = param.get("type", "")
    if param_type == "select" and param.get("enum"):
        return param["enum"][0]
    base_type = _resolve_type(param_type)
    if base_type in _EXAMPLE_VALUES:
        return _EXAMPLE_VALUES[base_type]
    return "示例值"


def _format_param_display(param: dict[str, Any]) -> str:
    """格式化单条参数显示"""
    name = param.get("variable", "")
    label = param.get("label", "")
    param_type = param.get("type", "")
    required = param.get("required")
    parts = [f"`{name}`"]
    if label:
        parts.append(f" {label}")
    if param_type:
        parts.append(f" ({_resolve_type(param_type)})")
    if required is True:
        parts.append(" ⚠️必填")
    elif required is False:
        parts.append(" 选填")
    if param_type == "select" and param.get("enum"):
        options = ", ".join(param["enum"])
        parts.append(f" 可选：[{options}]")
    return "".join(parts)


async def describe_flow_inputs(args: DescribeFlowInput) -> str:
    """获取流程信息及入参定义"""
    try:
        client = _get_client()
        result = await asyncio.to_thread(client.describe_flow_with_params, args.name)
        if not result.get("success"):
            err = result.get("error", {})
            return f"❌ 查询流程入参失败：{err.get('Message', err)}"

        data = result["data"]
        flow = data.get("flow", {})
        input_params = data.get("input_params", [])

        lines = [
            f"✅ 流程信息及入参 — `{flow.get('Name', args.name)}`\n",
            "**流程基本信息**\n",
            "| 属性 | 值 |",
            "|------|-----|",
            f"| 名称 | `{flow.get('Name', '')}` |",
            f"| ID | `{flow.get('Id', '')}` |",
            f"| 类型 | {flow.get('Type', '')} |",
            f"| 执行模式 | {flow.get('ExecutionMode', '')} |",
            f"| 描述 | {flow.get('Description', '-')} |",
            f"| 创建时间 | {flow.get('CreatedTime', '')} |",
            f"| 修改时间 | {flow.get('LastModifiedTime', '')} |",
        ]

        if not input_params:
            lines.append("")
            lines.append("---")
            lines.append("")
            lines.append("⚠️ **未检测到入参定义节点**")
            lines.append("")
            lines.append("请在 FNF Flow 中添加一个名为 `开始-入参说明` 的 **模板转换** 节点，")
            lines.append("template 字段填写参数定义的 JSON：")
            lines.append("")
            lines.append("```json")
            lines.append('{')
            lines.append('    "title": {"type": "string", "label": "标题", "required": 1},')
            lines.append('    "dept": {"type": "select", "enum": ["销售部", "技术部"]},')
            lines.append('    "count": {"type": "int", "label": "数量"},')
            lines.append('    "info": {"type": "object", "label": "详细信息"},')
            lines.append('    "tags": {"type": "array[string]", "label": "标签"},')
            lines.append('    "cover": {"type": "file", "label": "封面URL"},')
            lines.append('    "attachments": {"type": "file-list", "label": "附件列表"}')
            lines.append('}')
            lines.append("```")
        else:
            lines.append("")
            lines.append(f"**入参定义（共 {len(input_params)} 个）**\n")
            for i, param in enumerate(input_params, 1):
                lines.append(f"{i}. {_format_param_display(param)}")

            # Input JSON example
            lines.append("")
            lines.append("**示例入参 JSON**")
            lines.append("")
            json_example: dict[str, Any] = {}
            for param in input_params:
                json_example[param.get("variable", "")] = _make_example_value(param)
            lines.append(f"```json\n{json.dumps(json_example, ensure_ascii=False, indent=2)}\n```")

        return "\n".join(lines)
    except Exception as e:
        return f"❌ 查询流程入参失败：{e}"


async def list_flows(args: ListFlowsInput) -> str:
    """批量查询流程信息"""
    try:
        client = _get_client()
        result = await asyncio.to_thread(
            client.list_flows, limit=args.limit, next_token=args.next_token
        )
        if not result.get("success"):
            err = result.get("error", {})
            return f"❌ 查询流程列表失败：{err.get('Message', err)}"

        data = result["data"]
        flows = data.get("Flows", [])
        if not flows:
            return "暂无流程数据"

        md_lines = [f"**流程列表（共 {len(flows)} 个）**\n"]
        for i, flow in enumerate(flows, 1):
            md_lines.append(f"### {i}. {flow.get('Name', '未命名')}")
            md_lines.append(_flow_to_md(flow))
            md_lines.append("")

        if data.get("NextToken"):
            md_lines.append(f"> 📄 下一页 token: `{data['NextToken']}`")

        return "\n".join(md_lines)
    except Exception as e:
        return f"❌ 查询流程列表失败：{e}"
