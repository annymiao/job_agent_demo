from __future__ import annotations

import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"


def _read_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_candidates() -> list[dict]:
    payload = _read_json(SAMPLE_DATA_DIR / "candidates.json")
    return payload if isinstance(payload, list) else []


def load_jobs() -> list[dict]:
    payload = _read_json(SAMPLE_DATA_DIR / "jobs.json")
    return payload if isinstance(payload, list) else []


def get_candidate(candidate_id: str) -> dict | None:
    for candidate in load_candidates():
        if str(candidate.get("id")) == str(candidate_id):
            return candidate
    return None


def get_job(job_id: str) -> dict | None:
    for job in load_jobs():
        if str(job.get("id")) == str(job_id):
            return job
    return None

