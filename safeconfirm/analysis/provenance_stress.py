from __future__ import annotations

import random

from safeconfirm.analysis.source_analyzer import binding_slot_records
from safeconfirm.types.models import SourceAnalysisResultModel, SourceTrust


def apply_provenance_label_flip(
    analysis: SourceAnalysisResultModel,
    flip_rate: float,
    rng: random.Random,
) -> int:
    """Synthetic stress test: invert binding gap/source labels with probability flip_rate."""
    if flip_rate <= 0.0:
        return 0
    flipped = 0
    for record in binding_slot_records(analysis.slot_records):
        if rng.random() >= flip_rate:
            continue
        flipped += 1
        if record.authorization_gap:
            record.authorization_gap = False
            record.source = SourceTrust.TRUSTED_CONTACT
            record.risk_score = 0.1
        else:
            record.authorization_gap = True
            record.source = SourceTrust.UNTRUSTED_OBSERVATION
            record.risk_score = 1.0
    if flipped:
        _recompute_analysis_flags(analysis)
    return flipped


def _recompute_analysis_flags(analysis: SourceAnalysisResultModel) -> None:
    binding_records = binding_slot_records(analysis.slot_records)
    analysis.overall_risk = max((record.risk_score for record in binding_records), default=0.0)
    analysis.has_untrusted_binding = any(
        record.source in {SourceTrust.UNTRUSTED_OBSERVATION, SourceTrust.AGENT_INFERRED, SourceTrust.UNKNOWN}
        and record.authorization_gap
        for record in binding_records
    )
    analysis.has_role_only_binding = any(
        record.authorization_gap and record.slot.role_label is not None for record in binding_records
    )
