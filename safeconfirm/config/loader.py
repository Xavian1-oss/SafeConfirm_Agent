from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "defaults.yaml"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class SafeConfirmConfig:
    mode: str
    policy_backend: str
    risk_threshold_confirm: float
    risk_threshold_block: float
    never_allow_on_untrusted: bool
    enable_repair: bool
    max_repair_attempts: int
    registry_path: Path
    templates_path: Path
    simulated_confirmer: str
    experiences_path: Path
    training_cases_path: Path
    retrieval_top_k: int

    @classmethod
    def load(cls, config_path: str | Path | None = None) -> SafeConfirmConfig:
        path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        with path.open() as f:
            raw = yaml.safe_load(f)
        registry = _resolve_path(raw["registry_path"])
        templates = _resolve_path(raw["templates_path"])
        experiences = _resolve_path(raw["experiences_path"])
        training_cases = _resolve_path(raw["training_cases_path"])
        return cls(
            mode=os.getenv("SAFECONFIRM_MODE", raw["mode"]),
            policy_backend=os.getenv("SAFECONFIRM_POLICY", raw["policy_backend"]),
            risk_threshold_confirm=float(raw["risk_threshold_confirm"]),
            risk_threshold_block=float(raw["risk_threshold_block"]),
            never_allow_on_untrusted=bool(raw["never_allow_on_untrusted"]),
            enable_repair=bool(raw["enable_repair"]),
            max_repair_attempts=int(raw["max_repair_attempts"]),
            registry_path=registry,
            templates_path=templates,
            simulated_confirmer=raw["simulated_confirmer"],
            experiences_path=experiences,
            training_cases_path=training_cases,
            retrieval_top_k=int(raw.get("retrieval_top_k", 5)),
        )


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path
