from __future__ import annotations

from pathlib import Path

import yaml

from safeconfirm.types.models import (
    ConfirmationPayloadModel,
    ConfirmationResponseModel,
    InterventionRecordModel,
    InterventionType,
    SlotDisclosureModel,
    SourceTrust,
)

RISK_GAP_THRESHOLD = 0.5


def load_templates(templates_path: Path) -> dict[str, str]:
    with templates_path.open() as f:
        raw = yaml.safe_load(f)
    return {
        "vague_confirm": raw.get("vague_confirm", "").strip(),
        "source_aware_confirm": raw.get("source_aware_confirm", {}).get("default", "").strip(),
    }


def required_disclosures_for_record(record: InterventionRecordModel) -> list[str]:
    return [
        slot_record.slot.name
        for slot_record in record.slot_records
        if slot_record.slot.slot_class == "binding"
        and slot_record.authorization_gap
        and slot_record.slot.risk_weight >= RISK_GAP_THRESHOLD
    ]


def build_slot_disclosures(record: InterventionRecordModel) -> list[SlotDisclosureModel]:
    disclosures: list[SlotDisclosureModel] = []
    for slot_record in record.slot_records:
        if slot_record.slot.slot_class != "binding":
            continue
        if not slot_record.authorization_gap or slot_record.slot.risk_weight < RISK_GAP_THRESHOLD:
            continue
        evidence = slot_record.evidence[0] if slot_record.evidence else None
        source_detail = "unknown source"
        if evidence is not None:
            if evidence.observation_tool:
                source_detail = f"external content ({evidence.observation_tool})"
            elif evidence.message_role == "user":
                source_detail = "user message"
            else:
                source_detail = evidence.snippet[:80]
        disclosures.append(
            SlotDisclosureModel(
                slot_name=slot_record.slot.name,
                display_name=_display_name(slot_record.slot.name),
                value=str(slot_record.slot.value),
                source=slot_record.source,
                source_detail=source_detail,
                risk_note=_risk_note(slot_record.source),
            )
        )
    return disclosures


def build_confirmation_payload(
    record: InterventionRecordModel,
    intervention: InterventionType,
    templates: dict[str, str],
) -> ConfirmationPayloadModel:
    if intervention == InterventionType.VAGUE_CONFIRM:
        prompt = templates["vague_confirm"].replace("{{tool_name}}", record.tool_name)
        return ConfirmationPayloadModel(
            intervention="VAGUE_CONFIRM",
            tool_name=record.tool_name,
            action_summary=_action_summary(record),
            slot_disclosures=[],
            external_effect="The pending tool call will execute.",
            prompt_text=prompt,
            required_disclosures=[],
            laundering_safe=False,
        )

    disclosures = build_slot_disclosures(record)
    required = required_disclosures_for_record(record)
    external_effect = _external_effect(record, disclosures)
    prompt = _render_source_aware(
        templates["source_aware_confirm"],
        record.tool_name,
        _action_summary(record),
        disclosures,
        external_effect,
    )
    return ConfirmationPayloadModel(
        intervention="SOURCE_AWARE_CONFIRM",
        tool_name=record.tool_name,
        action_summary=_action_summary(record),
        slot_disclosures=disclosures,
        external_effect=external_effect,
        prompt_text=prompt,
        required_disclosures=required,
        laundering_safe=True,
    )


def validate_disclosure(payload: ConfirmationPayloadModel) -> bool:
    if payload.intervention == "VAGUE_CONFIRM":
        return True
    prompt_lower = payload.prompt_text.lower()
    disclosed_slots = {d.slot_name for d in payload.slot_disclosures}
    for slot_name in payload.required_disclosures:
        if slot_name not in disclosed_slots:
            return False
    for disclosure in payload.slot_disclosures:
        if disclosure.value not in payload.prompt_text:
            return False
        if disclosure.source == SourceTrust.UNTRUSTED_OBSERVATION and "untrusted" not in prompt_lower:
            if disclosure.source.value not in prompt_lower and "external" not in prompt_lower:
                return False
    return True


def is_confirmation_laundering(
    payload: ConfirmationPayloadModel,
    response: ConfirmationResponseModel,
    record: InterventionRecordModel,
) -> bool:
    if response.outcome != "approved":
        return False
    gap_slots = [
        slot_record
        for slot_record in record.slot_records
        if slot_record.slot.slot_class == "binding"
        and slot_record.authorization_gap
        and slot_record.slot.risk_weight >= RISK_GAP_THRESHOLD
    ]
    if not gap_slots:
        return False
    if payload.intervention == "VAGUE_CONFIRM":
        return True
    if payload.intervention == "SOURCE_AWARE_CONFIRM":
        for slot_record in gap_slots:
            if slot_record.slot.name not in payload.required_disclosures:
                return True
            if slot_record.slot.value_normalized not in payload.prompt_text.lower():
                if str(slot_record.slot.value).lower() not in payload.prompt_text.lower():
                    return True
            if slot_record.source == SourceTrust.UNTRUSTED_OBSERVATION:
                prompt_lower = payload.prompt_text.lower()
                if "untrusted" not in prompt_lower and "external" not in prompt_lower:
                    return True
        return not payload.laundering_safe
    return False


def _display_name(slot_name: str) -> str:
    mapping = {
        "recipients": "Recipient email(s)",
        "email": "Share with email",
        "file_id": "File ID",
        "permission": "Permission",
        "recipient": "Recipient account",
        "amount": "Amount",
    }
    return mapping.get(slot_name, slot_name)


def _risk_note(source: SourceTrust) -> str | None:
    if source in {SourceTrust.UNTRUSTED_OBSERVATION, SourceTrust.AGENT_INFERRED, SourceTrust.UNKNOWN}:
        return "This value is not from your original instruction or trusted contacts."
    return None


def _action_summary(record: InterventionRecordModel) -> str:
    return f"Run `{record.tool_name}` with the proposed parameters."


def _external_effect(record: InterventionRecordModel, disclosures: list[SlotDisclosureModel]) -> str:
    if not disclosures:
        return f"The tool `{record.tool_name}` will execute with the proposed parameters."
    parts = [f"{d.display_name} = {d.value}" for d in disclosures]
    return f"If you approve, `{record.tool_name}` will execute with: {', '.join(parts)}"


def _render_source_aware(
    template: str,
    tool_name: str,
    action_summary: str,
    disclosures: list[SlotDisclosureModel],
    external_effect: str,
) -> str:
    lines = [
        f"I am about to run `{tool_name}`.",
        "",
        f"Action: {action_summary}",
        "",
        "Critical parameters:",
    ]
    for disclosure in disclosures:
        lines.append(f"- {disclosure.display_name}: `{disclosure.value}`")
        lines.append(f"  Source: {disclosure.source_detail} ({disclosure.source.value})")
        if disclosure.risk_note:
            lines.append(f"  Note: {disclosure.risk_note}")
    lines.extend(
        [
            "",
            f"If you approve: {external_effect}",
            "",
            "Reply yes to proceed, no to cancel, or provide corrected values.",
        ]
    )
    return "\n".join(lines)
