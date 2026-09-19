from safeconfirm.analysis.provenance_stress import apply_provenance_label_flip
from safeconfirm.types.models import (
    CriticalSlotModel,
    SlotSourceRecordModel,
    SourceAnalysisResultModel,
    SourceTrust,
)


def _record(*, gap: bool, source: SourceTrust) -> SlotSourceRecordModel:
    slot = CriticalSlotModel(
        name="recipients",
        value="a@example.com",
        value_normalized="a@example.com",
        slot_type="email_list",
        risk_weight=1.0,
        slot_class="binding",
    )
    return SlotSourceRecordModel(
        slot=slot,
        source=source,
        evidence=[],
        authorization_gap=gap,
        risk_score=1.0 if gap else 0.1,
    )


def test_provenance_flip_zero_rate_is_noop() -> None:
    analysis = SourceAnalysisResultModel(
        slot_records=[_record(gap=True, source=SourceTrust.UNTRUSTED_OBSERVATION)],
        overall_risk=1.0,
        has_untrusted_binding=True,
        has_role_only_binding=False,
        action_type_authorized=True,
    )
    n = apply_provenance_label_flip(analysis, 0.0, __import__("random").Random(0))
    assert n == 0
    assert analysis.has_untrusted_binding


def test_provenance_flip_full_rate_recomputes_flags() -> None:
    analysis = SourceAnalysisResultModel(
        slot_records=[_record(gap=True, source=SourceTrust.UNTRUSTED_OBSERVATION)],
        overall_risk=1.0,
        has_untrusted_binding=True,
        has_role_only_binding=False,
        action_type_authorized=True,
    )
    n = apply_provenance_label_flip(analysis, 1.0, __import__("random").Random(42))
    assert n == 1
    assert not analysis.has_untrusted_binding
    assert analysis.overall_risk == 0.1
