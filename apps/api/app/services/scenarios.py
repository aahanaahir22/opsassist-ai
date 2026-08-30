from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


class ScenarioLoader:
    def __init__(self, root: Path) -> None:
        self.root = root

    def list(self) -> list[str]:
        return sorted(path.name for path in self.root.iterdir() if path.is_dir() and (path / "ground_truth.json").exists())

    def load(self, scenario_id: str) -> dict[str, Any]:
        folder = (self.root / scenario_id).resolve()
        if self.root.resolve() not in folder.parents or not folder.exists():
            raise FileNotFoundError(scenario_id)
        payload: dict[str, Any] = {"scenario_id": scenario_id}
        for name in ("ground_truth", "topology", "deployments", "expected_evidence"):
            payload[name] = json.loads((folder / f"{name}.json").read_text())
        payload["logs"] = [json.loads(line) for line in (folder / "logs.jsonl").read_text().splitlines() if line.strip()]
        payload["traces"] = [json.loads(line) for line in (folder / "traces.jsonl").read_text().splitlines() if line.strip()]
        with (folder / "metrics.csv").open(newline="") as handle:
            payload["metrics"] = list(csv.DictReader(handle))
        payload["manifest"] = self._parse_simple_yaml((folder / "scenario.yaml").read_text())
        return payload

    @staticmethod
    def _parse_simple_yaml(content: str) -> dict[str, str]:
        result: dict[str, str] = {}
        for line in content.splitlines():
            if line.strip() and not line.lstrip().startswith("#") and ":" in line:
                key, value = line.split(":", 1)
                result[key.strip()] = value.strip().strip('"')
        return result
