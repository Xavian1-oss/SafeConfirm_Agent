from pathlib import Path

import pytest

from safeconfirm.config.loader import SafeConfirmConfig
from safeconfirm.extraction.registry_loader import load_registry
from safeconfirm.extraction.slot_extractor import extract_critical_slots

REGISTRY_PATH = Path(__file__).resolve().parents[2] / "safeconfirm/data/tool_slot_registry.yaml"


@pytest.fixture
def registry():
    return load_registry(REGISTRY_PATH)


def test_send_email_extracts_recipients(registry):
    result = extract_critical_slots(
        "send_email",
        {
            "recipients": ["Supervisor@University.edu"],
            "subject": "Summary",
            "body": "Hello",
        },
        registry,
    )
    names = {slot.name for slot in result.critical_slots}
    assert "recipients" in names
    assert "body" in names
    recipient = next(s for s in result.critical_slots if s.name == "recipients")
    assert recipient.value_normalized == "supervisor@university.edu"


def test_unknown_tool_uses_fallback(registry):
    result = extract_critical_slots("unknown_tool", {"foo": "bar"}, registry)
    assert result.extraction_method == "fallback"
    assert len(result.critical_slots) == 1
    assert result.warnings
