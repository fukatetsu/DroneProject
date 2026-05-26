from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


SUPPORTED_TRANSITION_TYPES = {"auto", "manual", "duration"}


@dataclass(frozen=True)
class Transition:
    type: str
    seconds: Optional[float] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Transition":
        transition_type = str(data.get("type", "")).lower()
        if transition_type not in SUPPORTED_TRANSITION_TYPES:
            raise ValueError(f"Unsupported transition type: {transition_type}")

        seconds = None
        if transition_type == "duration":
            seconds_value = data.get("seconds")
            if seconds_value is None:
                raise ValueError("duration transition requires seconds")
            seconds = float(seconds_value)

        return cls(type=transition_type, seconds=seconds)


@dataclass(frozen=True)
class ScenarioStep:
    id: str
    comment: Optional[str]
    show_name: str
    transition: Transition

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScenarioStep":
        if "id" not in data or "show" not in data or "transition" not in data:
            raise ValueError("Scenario step must contain 'id', 'show', and 'transition'")

        return cls(
            id=str(data["id"]),
            comment=data.get("comment"),
            show_name=str(data["show"]),
            transition=Transition.from_dict(data["transition"]),
        )


class Scenario:
    def __init__(self, steps: Sequence[ScenarioStep]):
        if not steps:
            raise ValueError("Scenario must contain at least one show step")
        self._steps: List[ScenarioStep] = list(steps)
        self._current_index: int = 0

    @property
    def steps(self) -> List[ScenarioStep]:
        return list(self._steps)

    @property
    def current_step(self) -> ScenarioStep:
        return self._steps[self._current_index]

    @property
    def current_index(self) -> int:
        return self._current_index

    def advance(self) -> bool:
        if self._current_index + 1 < len(self._steps):
            self._current_index += 1
            return True
        return False

    def previous(self) -> bool:
        if self._current_index > 0:
            self._current_index -= 1
            return True
        return False

    def jump_to(self, step_id: str) -> bool:
        for index, step in enumerate(self._steps):
            if step.id == step_id:
                self._current_index = index
                return True
        return False

    def is_last_step(self) -> bool:
        return self._current_index >= len(self._steps) - 1

    def is_finished(self) -> bool:
        return self._current_index >= len(self._steps)

    @classmethod
    def load_from_file(cls, path: str) -> "Scenario":
        raw_path = Path(path)
        with raw_path.open("r", encoding="utf-8") as handle:
            content = json.load(handle)

        shows = content.get("shows")
        if not isinstance(shows, list):
            raise ValueError("Scenario JSON must contain a 'shows' list")

        steps = [ScenarioStep.from_dict(item) for item in shows]
        return cls(steps=steps)
