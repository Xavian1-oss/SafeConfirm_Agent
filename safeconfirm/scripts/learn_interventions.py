#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from safeconfirm.config.loader import SafeConfirmConfig
from safeconfirm.learning.experience_distiller import ExperienceDistiller, distill_to_store


def main() -> None:
    parser = argparse.ArgumentParser(description="Distill SafeConfirm intervention experiences from training cases.")
    parser.add_argument("--config", type=Path, default=None, help="Path to SafeConfirm config YAML.")
    parser.add_argument("--training-cases", type=Path, default=None, help="Path to training cases YAML.")
    parser.add_argument("--output", type=Path, default=None, help="Path to output experiences.jsonl.")
    args = parser.parse_args()

    config = SafeConfirmConfig.load(args.config)
    distiller = ExperienceDistiller(config)
    cases = distiller.load_training_cases(args.training_cases)
    experiences = distill_to_store(
        config=config,
        output_path=args.output or config.experiences_path,
        training_cases_path=args.training_cases,
    )
    print(f"Distilled {len(experiences)} experiences from {len(cases)} training cases.")
    print(f"Wrote: {args.output or config.experiences_path}")


if __name__ == "__main__":
    main()
