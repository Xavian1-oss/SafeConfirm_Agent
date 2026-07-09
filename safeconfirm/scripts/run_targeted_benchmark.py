#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from safeconfirm.config.loader import SafeConfirmConfig
from safeconfirm.evaluation.benchmark_cases import load_benchmark_cases
from safeconfirm.evaluation.metrics import save_targeted_run
from safeconfirm.evaluation.run_case import POLICY_PRESETS, run_benchmark_case


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SafeConfirm targeted L1 benchmark cases.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--cases", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=Path("runs/safeconfirm_l1"))
    parser.add_argument("--policy", choices=sorted(POLICY_PRESETS.keys()), action="append")
    parser.add_argument("--case-id", action="append")
    args = parser.parse_args()

    config = SafeConfirmConfig.load(args.config)
    cases_path = args.cases or (config.training_cases_path.parent / "benchmark_cases.yaml")
    cases = load_benchmark_cases(cases_path)
    if args.case_id:
        selected_ids = set(args.case_id)
        cases = [case for case in cases if case.id in selected_ids]

    policies = args.policy or sorted(POLICY_PRESETS.keys())
    for policy_id in policies:
        for case in cases:
            result = run_benchmark_case(case, policy_id, config=config)
            output_path = args.output / policy_id / f"{case.id}.json"
            save_targeted_run(output_path, result)
            print(f"{policy_id}\t{case.id}\tutility={result.utility}\tsecurity={result.security}")


if __name__ == "__main__":
    main()
