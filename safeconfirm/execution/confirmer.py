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


def get_confirmer() -> Confirmer:
    from safeconfirm.execution.llm_user_confirmer import LLMUserConfirmer

    return LLMUserConfirmer()
