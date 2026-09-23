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
    enable_repair: bool
    registry_path: Path
    templates_path: Path
    simulated_confirmer: str
    unknown_tool_policy: str
    provenance_flip_rate: float
    provenance_flip_seed: int

    @classmethod
    def load(cls, config_path: str | Path | None = None) -> SafeConfirmConfig:
        path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
        with path.open() as f:
            raw = yaml.safe_load(f)
        registry = _resolve_path(raw["registry_path"])
        templates = _resolve_path(raw["templates_path"])
        return cls(
            mode=os.getenv("SAFECONFIRM_MODE", raw["mode"]),
            policy_backend=os.getenv("SAFECONFIRM_POLICY", raw["policy_backend"]),
            risk_threshold_confirm=float(raw["risk_threshold_confirm"]),
            enable_repair=_env_bool("SAFECONFIRM_ENABLE_REPAIR", raw["enable_repair"]),
            registry_path=registry,
            templates_path=templates,
            simulated_confirmer=os.getenv("SAFECONFIRM_CONFIRMER", raw["simulated_confirmer"]),
            unknown_tool_policy=os.getenv(
                "SAFECONFIRM_UNKNOWN_TOOL_POLICY",
                raw.get("unknown_tool_policy", "conservative_confirm"),
            ),
            provenance_flip_rate=float(
                os.getenv("SAFECONFIRM_PROVENANCE_FLIP_RATE", raw.get("provenance_flip_rate", 0.0))
            ),
            provenance_flip_seed=int(
                os.getenv("SAFECONFIRM_PROVENANCE_FLIP_SEED", raw.get("provenance_flip_seed", 0))
            ),
        )


def _resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return bool(default)
    return value.strip().lower() in {"1", "true", "yes", "on"}
