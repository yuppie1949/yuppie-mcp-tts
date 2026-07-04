"""执行管理 MCP 工具 — 启动、停止、查询、历史"""

from __future__ import annotations

import asyncio
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


class StartExecutionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    flow_name: str = Field(..., min_length=1, description="流程名称")
    execution_name: Optional[str] = Field(None, description="执行名称（不指定则自动生成）")
    input_data: Optional[Dict[str, Any]] = Field(None, description="执行输入（JSON 字典）")


class StartSyncExecutionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    flow_name: str = Field(..., min_length=1, description="流程名称")
    execution_name: Optional[str] = Field(None, description="执行名称（不指定则自动生成）")
    input_data: Optional[Dict[str, Any]] = Field(None, description="执行输入（JSON 字典）")


class StopExecutionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    flow_name: str = Field(..., min_length=1, description="流程名称")
    execution_name: str = Field(..., min_length=1, description="执行名称")
    cause: Optional[str] = Field(None, description="停止原因")


class DescribeExecutionInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    flow_name: str = Field(..., min_length=1, description="流程名称")
    execution_name: str = Field(..., min_length=1, description="执行名称")


class ListExecutionsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    flow_name: str = Field(..., min_length=1, description="流程名称")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="返回数量")
    next_token: Optional[str] = Field(None, description="下一个查询令牌（分页使用）")


class GetExecutionHistoryInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    flow_name: str = Field(..., min_length=1, description="流程名称")
    execution_name: str = Field(..., min_length=1, description="执行名称")
    limit: Optional[int] = Field(None, ge=1, le=1000, description="返回数量")
    next_token: Optional[str] = Field(None, description="下一个查询令牌（分页使用）")


def _execution_to_md(execution: Dict[str, Any]) -> str:
    """单条执行记录格式化为 markdown"""
    lines = [
        f"- **执行名称**: `{execution.get('Name', '')}`",
        f"  - **状态**: {execution.get('Status', '')}",
        f"  - **开始时间**: {execution.get('StartedTime', '')}",
        f"  - **停止时间**: {execution.get('StoppedTime', '')}",
    ]
    if execution.get("Duration"):
        lines.append(f"  - **耗时**: {execution['Duration']}")
    return "\n".join(lines)


async def start_execution(args: StartExecutionInput) -> str:
    """异步启动一个流程执行"""
    try:
        client = _get_client()
        result = await asyncio.to_thread(
            client.start_execution,
            flow_name=args.flow_name,
            execution_name=args.execution_name,
            input_data=args.input_data,
        )
        if not result.get("success"):
            err = result.get("error", {})
            return f"❌ 启动执行失败：{err.get('Message', err)}"

        data = result["data"]
        return (
            f"✅ 执行已启动\n\n"
            f"| 属性 | 值 |\n"
            f"|------|-----|\n"
            f"| 流程名称 | `{data.get('FlowName', args.flow_name)}` |\n"
            f"| 执行名称 | `{data.get('Name', '')}` |\n"
            f"| 状态 | {data.get('Status', '')} |\n"
            f"| 开始时间 | {data.get('StartedTime', '')} |"
        )
    except Exception as e:
        return f"❌ 启动执行失败：{e}"


async def start_sync_execution(args: StartSyncExecutionInput) -> str:
    """同步启动一个流程执行"""
    try:
        client = _get_client()
        result = await asyncio.to_thread(
            client.start_sync_execution,
            flow_name=args.flow_name,
            execution_name=args.execution_name,
            input_data=args.input_data,
        )
        if not result.get("success"):
            err = result.get("error", {})
            return f"❌ 同步执行失败：{err.get('Message', err)}"

        data = result["data"]
        output = data.get("Output", "")
        return (
            f"✅ 同步执行完成\n\n"
            f"| 属性 | 值 |\n"
            f"|------|-----|\n"
            f"| 流程名称 | `{data.get('FlowName', args.flow_name)}` |\n"
            f"| 执行名称 | `{data.get('Name', '')}` |\n"
            f"| 状态 | {data.get('Status', '')} |\n"
            f"| 开始时间 | {data.get('StartedTime', '')} |\n"
            f"| 耗时 | {data.get('Duration', '-')} |\n"
            f"\n**执行输出**:\n```json\n{output}\n```"
            if output
            else ""
        )
    except Exception as e:
        return f"❌ 同步执行失败：{e}"


async def stop_execution(args: StopExecutionInput) -> str:
    """停止一个正在执行的流程"""
    try:
        client = _get_client()
        result = await asyncio.to_thread(
            client.stop_execution,
            flow_name=args.flow_name,
            execution_name=args.execution_name,
            cause=args.cause,
        )
        if not result.get("success"):
            err = result.get("error", {})
            return f"❌ 停止执行失败：{err.get('Message', err)}"

        data = result["data"]
        return (
            f"✅ 执行已停止\n\n"
            f"| 属性 | 值 |\n"
            f"|------|-----|\n"
            f"| 流程名称 | `{data.get('FlowName', args.flow_name)}` |\n"
            f"| 执行名称 | `{data.get('Name', args.execution_name)}` |\n"
            f"| 状态 | {data.get('Status', '')} |"
        )
    except Exception as e:
        return f"❌ 停止执行失败：{e}"


async def describe_execution(args: DescribeExecutionInput) -> str:
    """获取一次执行的状态信息"""
    try:
        client = _get_client()
        result = await asyncio.to_thread(
            client.describe_execution,
            flow_name=args.flow_name,
            execution_name=args.execution_name,
        )
        if not result.get("success"):
            err = result.get("error", {})
            return f"❌ 查询执行状态失败：{err.get('Message', err)}"

        data = result["data"]
        return (
            f"✅ 执行状态\n\n"
            f"| 属性 | 值 |\n"
            f"|------|-----|\n"
            f"| 流程名称 | `{data.get('FlowName', args.flow_name)}` |\n"
            f"| 执行名称 | `{data.get('Name', args.execution_name)}` |\n"
            f"| 状态 | {data.get('Status', '')} |\n"
            f"| 开始时间 | {data.get('StartedTime', '')} |\n"
            f"| 停止时间 | {data.get('StoppedTime', '')} |\n"
            f"| 耗时 | {data.get('Duration', '-')} |\n"
            f"| 触发方式 | {data.get('TriggerDetail', '-')} |"
        )
    except Exception as e:
        return f"❌ 查询执行状态失败：{e}"


async def list_executions(args: ListExecutionsInput) -> str:
    """获取一个流程的历史执行列表"""
    try:
        client = _get_client()
        result = await asyncio.to_thread(
            client.list_executions,
            flow_name=args.flow_name,
            limit=args.limit,
            next_token=args.next_token,
        )
        if not result.get("success"):
            err = result.get("error", {})
            return f"❌ 查询执行列表失败：{err.get('Message', err)}"

        data = result["data"]
        executions = data.get("Executions", [])
        if not executions:
            return f"流程 `{args.flow_name}` 暂无执行记录"

        md_lines = [f"**执行列表 — 流程 `{args.flow_name}`（共 {len(executions)} 个）**\n"]
        for i, exec_item in enumerate(executions, 1):
            md_lines.append(f"### {i}. {exec_item.get('Name', '未命名')}")
            md_lines.append(_execution_to_md(exec_item))
            md_lines.append("")

        if data.get("NextToken"):
            md_lines.append(f"> 📄 下一页 token: `{data['NextToken']}`")

        return "\n".join(md_lines)
    except Exception as e:
        return f"❌ 查询执行列表失败：{e}"


async def get_execution_history(args: GetExecutionHistoryInput) -> str:
    """获取一次执行的步骤详情"""
    try:
        client = _get_client()
        result = await asyncio.to_thread(
            client.get_execution_history,
            flow_name=args.flow_name,
            execution_name=args.execution_name,
            limit=args.limit,
            next_token=args.next_token,
        )
        if not result.get("success"):
            err = result.get("error", {})
            return f"❌ 查询执行历史失败：{err.get('Message', err)}"

        data = result["data"]
        events = data.get("Events", [])
        if not events:
            return f"执行 `{args.execution_name}` 暂无步骤记录"

        md_lines = [f"**执行历史 — `{args.execution_name}`（共 {len(events)} 个步骤）**\n"]
        for i, event in enumerate(events, 1):
            md_lines.append(
                f"**{i}. {event.get('Type', 'Unknown')}**  (ID: `{event.get('Id', '-')}`)"
            )
            md_lines.append(f"  - **时间**: {event.get('Time', '')}")
            if event.get("StepName"):
                md_lines.append(f"  - **步骤**: {event['StepName']}")
            if event.get("Input"):
                md_lines.append(f"  - **输入**: ```json\n{event['Input']}\n```")
            if event.get("Output"):
                md_lines.append(f"  - **输出**: ```json\n{event['Output']}\n```")
            md_lines.append("")

        if data.get("NextToken"):
            md_lines.append(f"> 📄 下一页 token: `{data['NextToken']}`")

        return "\n".join(md_lines)
    except Exception as e:
        return f"❌ 查询执行历史失败：{e}"
