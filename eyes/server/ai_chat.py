"""ai_chat.py — neural-network chat over the last N logs (server mode).

The AI sees the most recent 50 log entries from the LogStore and answers
questions about them through any OpenAI-compatible chat-completions API.

API endpoint / key are provided by the operator with:
    /ai_api <key-or-url>

Accepts either:
  * a bare API key (sk-...)                -> https://api.openai.com/v1
  * "KEY@https://host/v1"                  -> custom base URL + key
  * "https://host/v1/chat/completions"     -> keyless local server (llama.cpp, Ollama ...)

Only the Python standard library is used (urllib), so no extra pip installs.
"""

import json
import urllib.error
import urllib.request

DEFAULT_BASE = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"
CONTEXT_LOGS = 50          # how many latest logs the AI can see
TIMEOUT = 60               # seconds


def parse_api(value):
    """Return (base_url, api_key) from the operator's /ai_api argument."""
    value = (value or "").strip()
    if not value:
        return None, None
    if "@" in value and not value.startswith("sk-"):
        key, _, url = value.rpartition("@")
        return _norm_base(url), key.strip()
    if value.startswith("http://") or value.startswith("https://"):
        return _norm_base(value), ""
    return DEFAULT_BASE, value


def _norm_base(url):
    url = url.strip().rstrip("/")
    for suffix in ("/chat/completions", "/v1"):
        if url.endswith(suffix):
            url = url[: -len(suffix)]
    return url.rstrip("/") or DEFAULT_BASE


def build_context(store, limit=CONTEXT_LOGS):
    """Concatenate the newest `limit` log entries into one prompt block."""
    numbers = sorted(store.entries.keys())[-limit:]
    blocks = []
    for n in numbers:
        text, cat = store.entries[n]
        blocks.append(f"--- LOG #{n} [{str(cat).upper()}] ---\n{text}")
    return "\n".join(blocks) if blocks else "(no logs captured yet)"


def ask_ai(base_url, api_key, store, question, model=DEFAULT_MODEL):
    """Send the question + last 50 logs to the API. Returns (ok, answer)."""
    if not base_url:
        return False, "API not configured. Use: /ai_api <key-or-url>"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content":
                "You are the built-in analyst of 'Eyes of the Network', a Linux "
                "network monitor. You are shown the most recent numbered logs "
                "(categories: SUCCESS, SUSPICIOUS, BLOCKED/FAILED, MASKED, "
                "OWN NETWORK, BLUETOOTH). Answer concisely, reference log "
                "numbers when relevant, and flag anything dangerous."},
            {"role": "user", "content":
                f"Latest logs:\n\n{build_context(store)}\n\nQuestion: {question}"},
        ],
        "temperature": 0.2,
    }
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    if api_key:
        req.add_header("Authorization", f"Bearer {api_key}")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read().decode("utf-8", "replace"))
        answer = (body.get("choices") or [{}])[0].get("message", {}) \
                     .get("content", "").strip()
        if not answer:
            return False, f"Empty AI response: {json.dumps(body)[:300]}"
        return True, answer
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        return False, f"HTTP {e.code}: {detail}"
    except Exception as e:                      # noqa: BLE001
        return False, f"Request failed: {e}"
