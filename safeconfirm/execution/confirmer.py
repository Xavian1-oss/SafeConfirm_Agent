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


class AlwaysYesConfirmer:
    def respond(
        self,
        payload: ConfirmationPayloadModel,
        record: InterventionRecordModel,
        extra_args: dict,
    ) -> ConfirmationResponseModel:
        return ConfirmationResponseModel(outcome="approved", raw_text="yes")


class AlwaysNoConfirmer:
    def respond(
        self,
        payload: ConfirmationPayloadModel,
        record: InterventionRecordModel,
        extra_args: dict,
    ) -> ConfirmationResponseModel:
        return ConfirmationResponseModel(outcome="rejected", raw_text="no")


class OracleConfirmer:
    def respond(
        self,
        payload: ConfirmationPayloadModel,
        record: InterventionRecordModel,
        extra_args: dict,
    ) -> ConfirmationResponseModel:
        case = extra_args.get("safeconfirm", {}).get("benchmark_case", {})
        corrupted = case.get("corrupted_slots", {})
        trusted = case.get("trusted_binding", {})

        if corrupted:
            for slot_name, corrupted_value in corrupted.items():
                actual = record.tool_args.get(slot_name)
                if _values_match(actual, corrupted_value):
                    return ConfirmationResponseModel(outcome="rejected", raw_text="oracle_reject_corrupted")

        if any(r.authorization_gap for r in record.slot_records):
            return ConfirmationResponseModel(outcome="rejected", raw_text="oracle_reject_gap")

        if trusted:
            for slot_name, trusted_value in trusted.items():
                actual = record.tool_args.get(slot_name)
                if actual is None or not _values_match(actual, trusted_value):
                    return ConfirmationResponseModel(outcome="rejected", raw_text="oracle_reject_untrusted_mismatch")
            return ConfirmationResponseModel(outcome="approved", raw_text="oracle_approve_trusted")

        return ConfirmationResponseModel(outcome="approved", raw_text="oracle_approve")


def get_confirmer(name: str) -> Confirmer:
    if name == "always_yes":
        return AlwaysYesConfirmer()
    if name == "always_no":
        return AlwaysNoConfirmer()
    return OracleConfirmer()


def _values_match(actual: object, expected: object) -> bool:
    if isinstance(actual, list) and not isinstance(expected, list):
        expected = [expected]
    if isinstance(actual, list) and isinstance(expected, list):
        return sorted(str(v).lower() for v in actual) == sorted(str(v).lower() for v in expected)
    return str(actual).lower() == str(expected).lower()
