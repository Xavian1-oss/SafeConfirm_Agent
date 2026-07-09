from __future__ import annotations

from pathlib import Path

import yaml

from safeconfirm.types.models import BenchmarkCaseModel


def load_benchmark_cases(path: Path) -> list[BenchmarkCaseModel]:
    with path.open() as handle:
        raw = yaml.safe_load(handle)
    return [BenchmarkCaseModel.model_validate(item) for item in raw.get("cases", [])]
