"""Thin wrapper around Ollama's local REST API.
If Ollama is not running, every function returns None and the system
falls back to rule-based logic, so the project NEVER crashes."""
import json
import requests
from config import OLLAMA_URL, OLLAMA_MODEL


def ollama_available() -> bool:
    try:
        return requests.get(f"{OLLAMA_URL}/api/tags", timeout=2).status_code == 200
    except requests.RequestException:
        return False


def ask(prompt: str, system: str = "", as_json: bool = False, timeout: int = 120):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {"temperature": 0.3},
    }
    if as_json:
        payload["format"] = "json"
    try:
        r = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=timeout)
        r.raise_for_status()
        text = r.json()["response"].strip()
        return json.loads(text) if as_json else text
    except (requests.RequestException, json.JSONDecodeError, KeyError):
        return None
