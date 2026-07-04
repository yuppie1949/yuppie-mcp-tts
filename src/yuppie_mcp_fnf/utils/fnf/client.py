"""阿里云 FNF 客户端 — 封装 alibabacloud_fnf20190315 SDK

提供同步的方法接口，供 MCP 工具层通过 asyncio.to_thread 异步调用。
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from alibabacloud_credentials.client import Client as CredentialClient
from alibabacloud_credentials.models import Config as CredentialConfig
from alibabacloud_fnf20190315 import models as fnf_models
from alibabacloud_fnf20190315.client import Client as FNFClient
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from Tea.exceptions import TeaException, UnretryableException

# 默认超时配置（毫秒）
_DEFAULT_CONNECT_TIMEOUT = 10000  # 连接超时 10 秒
_DEFAULT_READ_TIMEOUT = 30000  # 读取超时 30 秒


def _make_runtime() -> util_models.RuntimeOptions:
    """创建带合理超时的 RuntimeOptions"""
    rt = util_models.RuntimeOptions()
    rt.connect_timeout = _DEFAULT_CONNECT_TIMEOUT
    rt.read_timeout = _DEFAULT_READ_TIMEOUT
    return rt


def _format_error(exception: Exception) -> Dict[str, Any]:
    """格式化 SDK 异常为结构化字典"""
    if isinstance(exception, TeaException):
        data = getattr(exception, "data", None)
        if isinstance(data, dict):
            return data
        return {
            "Code": getattr(exception, "code", "UnknownError"),
            "Message": getattr(exception, "message", str(exception)),
        }
    elif isinstance(exception, UnretryableException):
        return {
            "Code": "NetworkError",
            "Message": "网络请求失败，已达到最大重试次数",
        }
    else:
        return {"Code": "UnknownError", "Message": str(exception)}


def _strip_long_fields(data: Dict[str, Any]) -> Dict[str, Any]:
    """从响应中删除冗长的 Definition/FlowDefinition/Environment 字段"""
    result = data.copy()
    for field in ("Definition", "FlowDefinition", "Environment"):
        result.pop(field, None)
    return result


def _parse_flow_inputs_from_definition(definition_str: str) -> list[Dict[str, Any]]:
    """从 FDL Definition 解析出入参列表

    在 States 中找到 Name="开始-入参说明" 的 TemplateTransform 节点，
    取 Parameters.template 作为参数定义，key 为变量名，value 为元信息。

    Args:
        definition_str: Definition JSON 字符串（来自 API 响应）

    Returns:
        入参列表，每项含 variable + 类型定义（如果有）
    """
    if not definition_str:
        return []
    try:
        definition = json.loads(definition_str)
        for state in definition.get("States", []):
            if state.get("Name") != "开始-入参说明":
                continue
            if state.get("Action") != "Extensions:TemplateTransform":
                continue
            template = state.get("Parameters", {}).get("template", {})
            if not isinstance(template, dict):
                return []
            for v in template.values():
                if isinstance(v, dict) and v.get("required") == 1:
                    v["required"] = True
            result: list[Dict[str, Any]] = []
            for var_name, meta in template.items():
                entry: Dict[str, Any] = {"variable": var_name}
                if isinstance(meta, dict):
                    entry.update(meta)
                result.append(entry)
            return result
        return []
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
        return []


class AliyunFNFClient:
    """阿里云 FNF 客户端

    封装 FNF SDK，提供流程管理和执行管理接口。
    """

    def __init__(
        self,
        endpoint: str = "cn-hangzhou.fnf.aliyuncs.com",
        access_key_id: Optional[str] = None,
        access_key_secret: Optional[str] = None,
    ) -> None:
        if access_key_id and access_key_secret:
            credentials_config = CredentialConfig(
                type="access_key",
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
            )
            credential = CredentialClient(credentials_config)
        else:
            credential = CredentialClient()

        config = open_api_models.Config(credential=credential)
        config.endpoint = endpoint
        self.client = FNFClient(config)

    # ── 流程管理 ──

    def describe_flow(self, name: str) -> Dict[str, Any]:
        """获取流程信息"""
        try:
            request = fnf_models.DescribeFlowRequest(name=name)
            runtime = _make_runtime()
            response = self.client.describe_flow_with_options(request, runtime)
            data = _strip_long_fields(response.body.to_map())
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "error": _format_error(e)}

    def describe_flow_with_params(self, name: str) -> Dict[str, Any]:
        """获取流程信息及入参（包含 Definition 解析）

        在 describe_flow 的基础上，额外从 Definition 中解析出流程的入参列表。
        入参信息来源于`开始-入参说明`节点的 Parameters.template。

        Returns:
            success: True 时 data 包含：
                - flow (dict): 流程基本信息
                - input_params (list): 入参列表
        """
        try:
            request = fnf_models.DescribeFlowRequest(name=name)
            runtime = _make_runtime()
            response = self.client.describe_flow_with_options(request, runtime)
            raw = response.body.to_map()
            flow_data = _strip_long_fields(raw)
            definition_str = raw.get("Definition", "")
            input_params = _parse_flow_inputs_from_definition(definition_str)
            return {
                "success": True,
                "data": {
                    "flow": flow_data,
                    "input_params": input_params,
                },
            }
        except Exception as e:
            return {"success": False, "error": _format_error(e)}

    def list_flows(
        self,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """批量查询流程"""
        try:
            request = fnf_models.ListFlowsRequest()
            if limit is not None:
                request.limit = limit
            if next_token is not None:
                request.next_token = next_token
            runtime = _make_runtime()
            response = self.client.list_flows_with_options(request, runtime)
            data = _strip_long_fields(response.body.to_map())
            flows = data.get("Flows", [])
            data["Flows"] = [_strip_long_fields(f) for f in flows]
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "error": _format_error(e)}

    # ── 执行管理 ──

    def start_execution(
        self,
        flow_name: str,
        execution_name: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """异步启动流程执行"""
        try:
            request = fnf_models.StartExecutionRequest(flow_name=flow_name)
            if execution_name is not None:
                request.execution_name = execution_name
            if input_data is not None:
                request.input = json.dumps(input_data, ensure_ascii=False)
            runtime = _make_runtime()
            response = self.client.start_execution_with_options(request, runtime)
            data = _strip_long_fields(response.body.to_map())
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "error": _format_error(e)}

    def start_sync_execution(
        self,
        flow_name: str,
        execution_name: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """同步启动流程执行"""
        try:
            request = fnf_models.StartSyncExecutionRequest(flow_name=flow_name)
            if execution_name is not None:
                request.execution_name = execution_name
            if input_data is not None:
                request.input = json.dumps(input_data, ensure_ascii=False)
            runtime = _make_runtime()
            response = self.client.start_sync_execution_with_options(request, runtime)
            data = _strip_long_fields(response.body.to_map())
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "error": _format_error(e)}

    def stop_execution(
        self,
        flow_name: str,
        execution_name: str,
        cause: Optional[str] = None,
    ) -> Dict[str, Any]:
        """停止执行"""
        try:
            request = fnf_models.StopExecutionRequest(
                flow_name=flow_name,
                execution_name=execution_name,
            )
            if cause is not None:
                request.cause = cause
            runtime = _make_runtime()
            response = self.client.stop_execution_with_options(request, runtime)
            data = _strip_long_fields(response.body.to_map())
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "error": _format_error(e)}

    def describe_execution(
        self,
        flow_name: str,
        execution_name: str,
    ) -> Dict[str, Any]:
        """获取执行状态"""
        try:
            request = fnf_models.DescribeExecutionRequest(
                flow_name=flow_name,
                execution_name=execution_name,
            )
            runtime = _make_runtime()
            response = self.client.describe_execution_with_options(request, runtime)
            data = _strip_long_fields(response.body.to_map())
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "error": _format_error(e)}

    def list_executions(
        self,
        flow_name: str,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取流程的历史执行列表"""
        try:
            request = fnf_models.ListExecutionsRequest(flow_name=flow_name)
            if limit is not None:
                request.limit = limit
            if next_token is not None:
                request.next_token = next_token
            runtime = _make_runtime()
            response = self.client.list_executions_with_options(request, runtime)
            data = _strip_long_fields(response.body.to_map())
            executions = data.get("Executions", [])
            data["Executions"] = [_strip_long_fields(e) for e in executions]
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "error": _format_error(e)}

    def get_execution_history(
        self,
        flow_name: str,
        execution_name: str,
        limit: Optional[int] = None,
        next_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取执行步骤详情"""
        try:
            request = fnf_models.GetExecutionHistoryRequest(
                flow_name=flow_name,
                execution_name=execution_name,
            )
            if limit is not None:
                request.limit = limit
            if next_token is not None:
                request.next_token = next_token
            runtime = _make_runtime()
            response = self.client.get_execution_history_with_options(request, runtime)
            data = _strip_long_fields(response.body.to_map())
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "error": _format_error(e)}
