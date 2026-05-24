from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "mock" / "benchmark" / "labels.json"


def main() -> int:
    labels = json.loads(LABELS.read_text(encoding="utf-8"))
    print("Benchmark labels loaded:", len(labels))
    print("Run the backend, then trigger /api/expenses/{id}/agent-review for seeded examples to compute live metrics.")
    print("Tracked metrics: overall accuracy, false pass rate, false reject rate, human review rate, policy citation accuracy, tool success rate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
