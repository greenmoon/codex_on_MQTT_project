#!/usr/bin/env python3
"""Export the local live state as a small public-safe dashboard snapshot."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent


def mask_id(value):
    text = str(value)
    return text[:7] + "••••" + text[-2:] if len(text) > 11 else "••••"


with urlopen("http://127.0.0.1:8765/api/state", timeout=5) as response:
    state = json.load(response)

state["generated_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
state["broker_connected"] = False
state["broker"] = "Public-safe verified snapshot"
state.pop("broker_error", None)
for project in state["projects"].values():
    payload = project.get("last_payload")
    if isinstance(payload, dict) and "id" in payload:
        payload["id"] = mask_id(payload["id"])
    project["raw_payload"] = ""
    project["last_epoch"] = 0
    project["age_s"] = None
    project["status"] = "VERIFIED"
    project["history"] = project.get("history", [])[-60:]

(ROOT / "snapshot.json").write_text(
    json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(f'Exported public-safe snapshot: {state["generated_at"]}')
