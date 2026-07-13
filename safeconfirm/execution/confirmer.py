from __future__ import annotations

from safeconfirm.execution.llm_user_confirmer import LLMUserConfirmer
from safeconfirm.types.models import ConfirmationPayloadModel, ConfirmationResponseModel, InterventionRecordModel


class Confirmer:
    def respond(
        self,
        payload: ConfirmationPayloadModel,
        record: InterventionRecordModel,
        extra_args: dict,
    ) -> ConfirmationResponseModel: ...


def get_confirmer() -> Confirmer:
    return LLMUserConfirmer()
