from __future__ import annotations

import json
from pathlib import Path

from safeconfirm.types.models import ExperienceModel


class ExperienceStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> list[ExperienceModel]:
        if not self.path.exists():
            return []
        experiences: list[ExperienceModel] = []
        with self.path.open() as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                experiences.append(ExperienceModel.model_validate(json.loads(line)))
        return experiences

    def save(self, experiences: list[ExperienceModel]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w") as handle:
            for experience in experiences:
                handle.write(json.dumps(experience.model_dump(mode="json"), ensure_ascii=False))
                handle.write("\n")

    def append(self, experiences: list[ExperienceModel]) -> None:
        existing = self.load()
        existing.extend(experiences)
        self.save(existing)
