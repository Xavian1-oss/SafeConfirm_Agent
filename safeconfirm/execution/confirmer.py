from __future__ import annotations

from typing import Protocol

from safeconfirm.types.models import ConfirmationPayloadModel, ConfirmationResponseModel, InterventionRecordModel


class Confirmer(Protocol):
    def respond(
        self,
        payload: ConfirmationPayloadModel,
        record: InterventionRecordModel,
        extra_args: dict,
    ) -> ConfirmationResponseModel: ...


def get_confirmer(kind: str = "llm_user", model: str | None = None) -> Confirmer:
    if kind in ("oracle", "oracle_strict"):
        from safeconfirm.execution.oracle_confirmer import StrictOracleConfirmer

        return StrictOracleConfirmer()
    if kind == "compliant_llm":
        from safeconfirm.execution.llm_user_confirmer import CompliantLLMUserConfirmer

        return CompliantLLMUserConfirmer(model=model)
    from safeconfirm.execution.llm_user_confirmer import LLMUserConfirmer

    return LLMUserConfirmer(model=model)
