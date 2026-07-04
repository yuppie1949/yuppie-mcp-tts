"""tools 层 BaseModel 输入校验测试"""

import pytest
from pydantic import ValidationError

from yuppie_mcp_fnf.tools.flows import DescribeFlowInput, ListFlowsInput
from yuppie_mcp_fnf.tools.executions import (
    StartExecutionInput,
    StartSyncExecutionInput,
    StopExecutionInput,
    DescribeExecutionInput,
    ListExecutionsInput,
    GetExecutionHistoryInput,
)


# ── 流程管理 ──


def test_describe_flow_required():
    with pytest.raises(ValidationError):
        DescribeFlowInput()


def test_describe_flow_accepts_valid_input():
    args = DescribeFlowInput(name="my_flow")
    assert args.name == "my_flow"


def test_describe_flow_strips_whitespace():
    args = DescribeFlowInput(name="  my_flow  ")
    assert args.name == "my_flow"


def test_describe_flow_forbids_extra():
    with pytest.raises(ValidationError):
        DescribeFlowInput(name="flow", extra_field="bad")


def test_list_flows_defaults():
    args = ListFlowsInput()
    assert args.limit is None
    assert args.next_token is None


def test_list_flows_with_pagination():
    args = ListFlowsInput(limit=10, next_token="abc123")
    assert args.limit == 10
    assert args.next_token == "abc123"


def test_list_flows_rejects_invalid_limit():
    with pytest.raises(ValidationError):
        ListFlowsInput(limit=0)


# ── 执行管理 ──


def test_start_execution_required():
    with pytest.raises(ValidationError):
        StartExecutionInput()


def test_start_execution_accepts_valid():
    args = StartExecutionInput(flow_name="my_flow")
    assert args.flow_name == "my_flow"


def test_start_execution_with_all_fields():
    args = StartExecutionInput(
        flow_name="my_flow",
        execution_name="exec_001",
        input_data={"key": "value"},
    )
    assert args.execution_name == "exec_001"
    assert args.input_data == {"key": "value"}


def test_start_sync_execution_required():
    with pytest.raises(ValidationError):
        StartSyncExecutionInput()


def test_stop_execution_required():
    with pytest.raises(ValidationError):
        StopExecutionInput()


def test_stop_execution_accepts_valid():
    args = StopExecutionInput(flow_name="my_flow", execution_name="exec_001")
    assert args.cause is None


def test_stop_execution_with_cause():
    args = StopExecutionInput(
        flow_name="my_flow",
        execution_name="exec_001",
        cause="User canceled",
    )
    assert args.cause == "User canceled"


def test_describe_execution_required():
    with pytest.raises(ValidationError):
        DescribeExecutionInput()


def test_describe_execution_accepts_valid():
    args = DescribeExecutionInput(flow_name="my_flow", execution_name="exec_001")
    assert args.flow_name == "my_flow"
    assert args.execution_name == "exec_001"


def test_list_executions_required():
    with pytest.raises(ValidationError):
        ListExecutionsInput()


def test_list_executions_with_pagination():
    args = ListExecutionsInput(flow_name="my_flow", limit=20, next_token="token")
    assert args.flow_name == "my_flow"
    assert args.limit == 20
    assert args.next_token == "token"


def test_get_execution_history_required():
    with pytest.raises(ValidationError):
        GetExecutionHistoryInput()


def test_get_execution_history_accepts_valid():
    args = GetExecutionHistoryInput(flow_name="my_flow", execution_name="exec_001")
    assert args.limit is None
    assert args.next_token is None


def test_all_inputs_forbid_extra():
    inputs = [
        DescribeFlowInput(name="x"),
        ListFlowsInput(),
        StartExecutionInput(flow_name="x"),
        StopExecutionInput(flow_name="x", execution_name="x"),
        DescribeExecutionInput(flow_name="x", execution_name="x"),
        ListExecutionsInput(flow_name="x"),
        GetExecutionHistoryInput(flow_name="x", execution_name="x"),
    ]
    for inp in inputs:
        assert inp.model_config.get("extra") == "forbid"
