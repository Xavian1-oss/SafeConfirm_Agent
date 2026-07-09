from pathlib import Path

import pytest

from safeconfirm.config.loader import SafeConfirmConfig
from safeconfirm.extraction.registry_loader import load_registry
from safeconfirm.learning.experience_distiller import distill_to_store
from safeconfirm.learning.experience_store import ExperienceStore
from safeconfirm.learning.group_comparator import GroupComparator
from safeconfirm.policy.retrieval_policy import RetrievalPolicy
from safeconfirm.policy.rule_policy import rule_v1_select, select_intervention
from safeconfirm.types.models import (
    CriticalSlotModel,
    InterventionType,
    SlotSourceRecordModel,
    SourceAnalysisResultModel,
    SourceTrust,
)
from safeconfirm.verifier.intervention_verifier import InterventionVerifier, VerificationContext

REGISTRY_PATH = Path(__file__).resolve().parents[2] / "safeconfirm/data/tool_slot_registry.yaml"
TRAINING_CASES_PATH = Path(__file__).resolve().parents[2] / "safeconfirm/data/seed_training_cases.yaml"


@pytest.fixture
def registry():
    return load_registry(REGISTRY_PATH)


@pytest.fixture
def config(tmp_path):
    base = SafeConfirmConfig.load()
    return SafeConfirmConfig(
        mode=base.mode,
        policy_backend="retrieval",
        risk_threshold_confirm=base.risk_threshold_confirm,
        risk_threshold_block=base.risk_threshold_block,
        never_allow_on_untrusted=base.never_allow_on_untrusted,
        enable_repair=base.enable_repair,
        max_repair_attempts=base.max_repair_attempts,
        registry_path=base.registry_path,
        templates_path=base.templates_path,
        simulated_confirmer=base.simulated_confirmer,
        experiences_path=tmp_path / "experiences.jsonl",
        training_cases_path=TRAINING_CASES_PATH,
        retrieval_top_k=5,
    )


def _analysis(
    tool_name: str,
    *,
    has_untrusted: bool = True,
    role_binding: bool = False,
    action_category: str | None = None,
) -> SourceAnalysisResultModel:
    slot = CriticalSlotModel(
        name="recipient" if tool_name == "send_money" else "file_id",
        value="attacker_value",
        value_normalized="attacker_value",
        slot_type="account" if tool_name == "send_money" else "file_id",
        risk_weight=1.0,
        role_label="supervisor" if role_binding else None,
    )
    slot_record = SlotSourceRecordModel(
        slot=slot,
        source=SourceTrust.UNTRUSTED_OBSERVATION,
        evidence=[],
        authorization_gap=True,
        risk_score=1.0,
    )
    return SourceAnalysisResultModel(
        slot_records=[slot_record],
        overall_risk=1.0,
        has_untrusted_binding=has_untrusted,
        has_role_only_binding=role_binding,
        action_type_authorized=True,
    )


def test_verifier_disqualifies_allow_and_vague_on_gap(registry):
    verifier = InterventionVerifier()
    analysis = _analysis("send_email")
    allow = verifier.score(analysis, InterventionType.ALLOW, registry, "send_email")
    vague = verifier.score(analysis, InterventionType.VAGUE_CONFIRM, registry, "send_email")
    assert allow.disqualified is True
    assert vague.disqualified is True


def test_group_comparator_prefers_block_for_financial_gap(registry):
    verifier = InterventionVerifier()
    analysis = _analysis("send_money")
    context = VerificationContext(
        safe_interventions={"BLOCK", "SOURCE_AWARE_CONFIRM"},
        unsafe_interventions={"ALLOW"},
        laundering_interventions={"VAGUE_CONFIRM"},
    )
    scores = {
        InterventionType.BLOCK: verifier.score(analysis, InterventionType.BLOCK, registry, "send_money", context),
        InterventionType.SOURCE_AWARE_CONFIRM: verifier.score(
            analysis, InterventionType.SOURCE_AWARE_CONFIRM, registry, "send_money", context
        ),
    }
    result = GroupComparator().compare(scores)
    assert result.winner == InterventionType.BLOCK


def test_distiller_produces_at_least_ten_experiences(config):
    experiences = distill_to_store(config=config, output_path=config.experiences_path)
    assert len(experiences) >= 10
    assert all(experience.intervention_choice for experience in experiences)
    stored = ExperienceStore(config.experiences_path).load()
    assert len(stored) == len(experiences)


def test_retrieval_changes_holdout_decisions_vs_rule_v1(config, registry):
    distill_to_store(config=config, output_path=config.experiences_path)
    retrieval = RetrievalPolicy(ExperienceStore(config.experiences_path), top_k=5)

    holdout_cases = [
        ("send_money", _analysis("send_money")),
        ("delete_file", _analysis("delete_file")),
    ]
    changes = 0
    for tool_name, analysis in holdout_cases:
        rule_choice = rule_v1_select(analysis, registry, tool_name, True, True)
        retrieval_choice = retrieval.select_intervention(analysis, registry, tool_name, True, True)
        assert rule_choice == InterventionType.SOURCE_AWARE_CONFIRM
        assert retrieval_choice == InterventionType.BLOCK
        changes += 1
    assert changes >= 2


def test_select_intervention_uses_retrieval_backend(config, registry):
    distill_to_store(config=config, output_path=config.experiences_path)
    retrieval = RetrievalPolicy(ExperienceStore(config.experiences_path), top_k=5)
    analysis = _analysis("send_money")
    selected = select_intervention(
        analysis,
        registry,
        "send_money",
        "retrieval",
        True,
        True,
        retrieval,
    )
    assert selected == InterventionType.BLOCK
