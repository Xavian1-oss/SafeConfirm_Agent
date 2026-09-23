"""Runtime context for repair feasibility checks before policy selects REPAIR."""

from __future__ import annotations

from dataclasses import dataclass

from agentdojo.functions_runtime import FunctionsRuntime, TaskEnvironment


@dataclass(frozen=True)
class RepairPreflight:
    runtime: FunctionsRuntime
    env: TaskEnvironment
