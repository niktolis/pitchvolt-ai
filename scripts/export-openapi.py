"""Export the FastAPI contract deterministically for generated TypeScript types."""

from __future__ import annotations

import json
from pathlib import Path

from matchpulse.api import app

TARGET = Path(__file__).resolve().parents[1] / "web" / "openapi.json"
TARGET.write_text(
    json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
print(TARGET)
