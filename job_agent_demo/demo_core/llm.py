from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")
load_dotenv()


def llm_ready() -> bool:
    return bool(os.getenv("OPENAI_BASE_URL", "").strip() and os.getenv("OPENAI_API_KEY", "").strip())


def resolve_model() -> str:
    return os.getenv("JOB_AGENT_DEMO_MODEL", "gpt-5.4")


def call_demo_llm(messages: list[dict[str, str]], model: str | None = None, timeout_seconds: int = 60) -> str:
    base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not base_url or not api_key:
        raise RuntimeError("LLM configuration missing. Set OPENAI_BASE_URL and OPENAI_API_KEY.")

    response = requests.post(
        f"{base_url.rstrip('/')}/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model or resolve_model(),
            "messages": messages,
            "temperature": 0.4,
        },
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    payload = response.json()
    choices = payload.get("choices", [])
    if not choices:
        return ""
    message = choices[0].get("message", {})
    return str(message.get("content", "")).strip()


def polish_section(section_name: str, payload: dict[str, Any]) -> str:
    prompt = (
        "You are polishing the narrative of a public demo for a job-search decision assistant.\n"
        "Rules:\n"
        "- Keep the output concise and useful.\n"
        "- Do not mention prompts, internal systems, skills, or agents.\n"
        "- Use plain English bullets only.\n"
        "- Stay grounded in the structured payload.\n\n"
        f"Section: {section_name}\n"
        f"Payload:\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        "Write 4 to 6 bullets."
    )
    return call_demo_llm(
        [
            {
                "role": "system",
                "content": "You write crisp, operator-style hiring guidance for a public product demo.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]
    )
