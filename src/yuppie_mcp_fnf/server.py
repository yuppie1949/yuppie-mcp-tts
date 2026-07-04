"""阿里云 FNF MCP Server 主入口"""

from __future__ import annotations

import os
from typing import Annotated, Any, Dict, Optional

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from . import __version__
from .tools import executions, flows

mcp = FastMCP(
    "fnf_mcp",
    instructions=(
        "阿里云 FNF (Serverless 工作流) MCP Server。"
        "提供流程管理（查询流程、列表）和执行管理（启动/停止执行、查询状态、"
        "执行历史）功能。"
        "使用 fnf_describe_flow_inputs 可获取流程入参定义及示例 JSON。"
    ),
)
mcp._mcp_server.version = __version__


# ═══════════════════════════════════════════
# 流程管理
# ═══════════════════════════════════════════


@mcp.tool(
    name="fnf_describe_flow",
    annotations=ToolAnnotations(
        title="获取 FNF 流程信息",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_describe_flow(
    name: Annotated[str, "流程名称"],
) -> str:
    """获取一个 FNF 流程的详细信息，包括类型、执行模式、描述、创建时间等。"""
    return await flows.describe_flow(flows.DescribeFlowInput(name=name))


@mcp.tool(
    name="fnf_describe_flow_inputs",
    annotations=ToolAnnotations(
        title="获取 FNF 流程信息及入参",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_describe_flow_inputs(
    name: Annotated[str, "流程名称"],
) -> str:
    """获取 FNF 流程信息，并从 Definition 中解析出入参定义（含示例 JSON）。"""
    return await flows.describe_flow_inputs(flows.DescribeFlowInput(name=name))


@mcp.tool(
    name="fnf_list_flows",
    annotations=ToolAnnotations(
        title="查询 FNF 流程列表",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_list_flows(
    limit: Annotated[Optional[int], "返回数量，取值范围 [1, 1000)，默认 60"] = None,
    next_token: Annotated[Optional[str], "下一个查询令牌（分页使用）"] = None,
) -> str:
    """批量查询 FNF 流程信息。支持分页。"""
    return await flows.list_flows(flows.ListFlowsInput(limit=limit, next_token=next_token))


# ═══════════════════════════════════════════
# 执行管理
# ═══════════════════════════════════════════


@mcp.tool(
    name="fnf_start_execution",
    annotations=ToolAnnotations(
        title="异步启动 FNF 流程执行",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_start_execution(
    flow_name: Annotated[str, "流程名称"],
    execution_name: Annotated[Optional[str], "执行名称（不指定则自动生成）"] = None,
    input_data: Annotated[Optional[Dict[str, Any]], "执行输入（JSON 字典）"] = None,
) -> str:
    """异步启动一个 FNF 流程的执行。"""
    return await executions.start_execution(
        executions.StartExecutionInput(
            flow_name=flow_name,
            execution_name=execution_name,
            input_data=input_data,
        )
    )


@mcp.tool(
    name="fnf_start_sync_execution",
    annotations=ToolAnnotations(
        title="同步启动 FNF 流程执行",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_start_sync_execution(
    flow_name: Annotated[str, "流程名称"],
    execution_name: Annotated[Optional[str], "执行名称（不指定则自动生成）"] = None,
    input_data: Annotated[Optional[Dict[str, Any]], "执行输入（JSON 字典）"] = None,
) -> str:
    """同步启动一个 FNF 流程的执行，等待执行完成并返回结果。"""
    return await executions.start_sync_execution(
        executions.StartSyncExecutionInput(
            flow_name=flow_name,
            execution_name=execution_name,
            input_data=input_data,
        )
    )


@mcp.tool(
    name="fnf_stop_execution",
    annotations=ToolAnnotations(
        title="停止 FNF 流程执行",
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    ),
)
async def tool_stop_execution(
    flow_name: Annotated[str, "流程名称"],
    execution_name: Annotated[str, "执行名称"],
    cause: Annotated[Optional[str], "停止原因"] = None,
) -> str:
    """停止一个正在执行的 FNF 流程。"""
    return await executions.stop_execution(
        executions.StopExecutionInput(
            flow_name=flow_name,
            execution_name=execution_name,
            cause=cause,
        )
    )


@mcp.tool(
    name="fnf_describe_execution",
    annotations=ToolAnnotations(
        title="查询 FNF 执行状态",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_describe_execution(
    flow_name: Annotated[str, "流程名称"],
    execution_name: Annotated[str, "执行名称"],
) -> str:
    """获取一次 FNF 流程执行的状态信息，包括状态、耗时等。"""
    return await executions.describe_execution(
        executions.DescribeExecutionInput(
            flow_name=flow_name,
            execution_name=execution_name,
        )
    )


@mcp.tool(
    name="fnf_list_executions",
    annotations=ToolAnnotations(
        title="查询 FNF 执行历史列表",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_list_executions(
    flow_name: Annotated[str, "流程名称"],
    limit: Annotated[Optional[int], "返回数量"] = None,
    next_token: Annotated[Optional[str], "下一个查询令牌（分页使用）"] = None,
) -> str:
    """获取一个 FNF 流程的历史执行列表。支持分页。"""
    return await executions.list_executions(
        executions.ListExecutionsInput(
            flow_name=flow_name,
            limit=limit,
            next_token=next_token,
        )
    )


@mcp.tool(
    name="fnf_get_execution_history",
    annotations=ToolAnnotations(
        title="获取 FNF 执行步骤详情",
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
)
async def tool_get_execution_history(
    flow_name: Annotated[str, "流程名称"],
    execution_name: Annotated[str, "执行名称"],
    limit: Annotated[Optional[int], "返回数量"] = None,
    next_token: Annotated[Optional[str], "下一个查询令牌（分页使用）"] = None,
) -> str:
    """获取一次 FNF 流程执行的步骤详情（执行历史）。"""
    return await executions.get_execution_history(
        executions.GetExecutionHistoryInput(
            flow_name=flow_name,
            execution_name=execution_name,
            limit=limit,
            next_token=next_token,
        )
    )


def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "streamable-http":
        mcp.settings.port = int(os.getenv("MCP_PORT", "8000"))
        mcp.run(transport="streamable-http")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
