from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app import db

SEED_CHALLENGES_PATH = Path(__file__).resolve().parent / "data" / "challenges.json"


def load_seed_challenges() -> list[dict[str, Any]]:
    return json.loads(SEED_CHALLENGES_PATH.read_text(encoding="utf-8"))


def seed_challenges_if_empty() -> None:
    if db.count_challenges() > 0:
        return

    for challenge in load_seed_challenges():
        db.upsert_challenge(challenge)

