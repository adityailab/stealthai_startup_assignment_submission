# app/services/llm.py
from __future__ import annotations
from typing import List, Dict, Optional
import os
import httpx
from app.core.config import settings

OPENAI_BASE = os.getenv("OPENAI_BASE", "https://api.openai.com/v1")
HF_API_BASE = os.getenv("HF_API_BASE", "https://api-inference.huggingface.co/models")

# ---------------- OpenAI ----------------
def _openai_chat(messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not configured")
    payload = {
        "model": model or settings.OPENAI_MODEL or "gpt-4o-mini",
        "messages": messages,
        "temperature": 0.2,
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    with httpx.Client(timeout=60) as client:
        r = client.post(f"{OPENAI_BASE}/chat/completions", json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
    return data["choices"][0]["message"]["content"]

# ---------------- Ollama (local) ----------------
def _ollama_chat(messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
    base = settings.OLLAMA_HOST or "http://localhost:11434"
    mdl = model or settings.OLLAMA_MODEL or "tinyllama:latest"

    payload = {
        "model": mdl,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.2},
    }

    # generous timeouts; pulling a big model can take minutes
    timeout = httpx.Timeout(connect=5.0, read=600.0, write=120.0, pool=5.0)

    # small retry loop for transient timeouts
    for attempt in range(3):
        try:
            with httpx.Client(timeout=timeout) as client:
                r = client.post(f"{base}/api/chat", json=payload)
                r.raise_for_status()
                data = r.json()
                return data["message"]["content"]
        except httpx.ReadTimeout:
            if attempt == 2:
                raise
        except httpx.HTTPStatusError as e:
            # surface useful info
            raise RuntimeError(f"Ollama error {e.response.status_code}: {e.response.text[:300]}") from e

# app/services/llm.py — HF section only
from app.core.config import settings
import httpx

def _hf_chat(messages, model: str | None = None) -> str:
    token = settings.HF_TOKEN
    if not token:
        raise RuntimeError("HF_TOKEN not configured")
    repo_id = model or settings.HF_MODEL_ID or "mistralai/Mistral-7B-Instruct-v0.2"
    api_base = (settings.HF_API_BASE or "https://api-inference.huggingface.co/models").rstrip("/")
    url = f"{api_base}/{repo_id}"
    headers = {"Authorization": f"Bearer {token}"}

    def to_prompt(msgs):
        parts = []
        for m in msgs:
            role = m.get("role", "user")
            if role == "system":
                parts.append(f"[SYSTEM]\n{m['content']}\n")
            elif role == "user":
                parts.append(f"[USER]\n{m['content']}\n")
            else:
                parts.append(f"[ASSISTANT]\n{m['content']}\n")
        parts.append("[ASSISTANT]\n")
        return "\n".join(parts)

    payload = {
        "inputs": to_prompt(messages),
        "parameters": {"temperature": 0.2, "max_new_tokens": 256, "return_full_text": False}
    }

    try:
        with httpx.Client(timeout=120) as client:
            r = client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        # Helpful error in your logs instead of a 500 stacktrace
        raise RuntimeError(
            f"HF API error {e.response.status_code} for {repo_id}. "
            f"Check HF_TOKEN and license access. Details: {e.response.text[:300]}"
        ) from e

    if isinstance(data, list) and data:
        return (data[0].get("generated_text") or "").strip()
    if isinstance(data, dict):
        if "generated_text" in data:
            return (data["generated_text"] or "").strip()
        if "choices" in data and data["choices"]:
            return (data["choices"][0].get("text") or "").strip()
    return ""

# ---------------- Hugging Face ----------------
#def _hf_chat(messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
    """
    Works with HF serverless Inference API or a private Inference Endpoint.
    Env:
      HF_TOKEN      - required
      HF_MODEL_ID   - default model id (e.g. mistralai/Mistral-7B-Instruct-v0.2)
      HF_API_BASE   - base URL (defaults to serverless endpoint)
    """
    token = settings.HF_TOKEN
    if not token:
        raise RuntimeError("HF_TOKEN not configured")
    repo_id = model or settings.HF_MODEL_ID or "mistralai/Mistral-7B-Instruct-v0.2"
    api_base = (settings.HF_API_BASE or "https://api-inference.huggingface.co/models").rstrip("/")
    url = f"{api_base}/{repo_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    # Convert chat messages to a simple instruct prompt many HF backends accept
    def to_prompt(msgs: List[Dict[str, str]]) -> str:
        parts = []
        for m in msgs:
            role = m.get("role", "user")
            if role == "system":
                parts.append(f"[SYSTEM]\n{m['content']}\n")
            elif role == "user":
                parts.append(f"[USER]\n{m['content']}\n")
            else:
                parts.append(f"[ASSISTANT]\n{m['content']}\n")
        parts.append("[ASSISTANT]\n")
        return "\n".join(parts)

    payload = {
        "inputs": to_prompt(messages),
        "parameters": {
            "temperature": 0.2,
            "max_new_tokens": 256,
            "return_full_text": False
        }
    }
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{HF_API_BASE.rstrip('/')}/{repo_id}"
    with httpx.Client(timeout=120) as client:
        r = client.post(url, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()

    # HF responses vary slightly by backend
    if isinstance(data, list) and data:
        return (data[0].get("generated_text") or "").strip()
    if isinstance(data, dict):
        if "generated_text" in data:
            return (data["generated_text"] or "").strip()
        if "choices" in data and data["choices"]:
            return (data["choices"][0].get("text") or "").strip()
    return ""

def _hf_chat(messages, model: str | None = None) -> str:
    token = settings.HF_TOKEN
    if not token:
        raise RuntimeError("HF_TOKEN not configured")
    repo_id = model or settings.HF_MODEL_ID or "mistralai/Mistral-7B-Instruct-v0.2"
    api_base = (settings.HF_API_BASE or "https://api-inference.huggingface.co/models").rstrip("/")
    url = f"{api_base}/{repo_id}"
    headers = {"Authorization": f"Bearer {token}"}

    def to_prompt(msgs):
        parts = []
        for m in msgs:
            role = m.get("role", "user")
            if role == "system":
                parts.append(f"[SYSTEM]\n{m['content']}\n")
            elif role == "user":
                parts.append(f"[USER]\n{m['content']}\n")
            else:
                parts.append(f"[ASSISTANT]\n{m['content']}\n")
        parts.append("[ASSISTANT]\n")
        return "\n".join(parts)

    payload = {
        "inputs": to_prompt(messages),
        "parameters": {"temperature": 0.2, "max_new_tokens": 256, "return_full_text": False}
    }

    try:
        with httpx.Client(timeout=120) as client:
            r = client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        # Helpful error in your logs instead of a 500 stacktrace
        raise RuntimeError(
            f"HF API error {e.response.status_code} for {repo_id}. "
            f"Check HF_TOKEN and license access. Details: {e.response.text[:300]}"
        ) from e

    if isinstance(data, list) and data:
        return (data[0].get("generated_text") or "").strip()
    if isinstance(data, dict):
        if "generated_text" in data:
            return (data["generated_text"] or "").strip()
        if "choices" in data and data["choices"]:
            return (data["choices"][0].get("text") or "").strip()
    return ""
# ---------------- Public API ----------------
def chat(
    messages: List[Dict[str, str]],
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """
    provider:
      - "openai": OpenAI Chat Completions
      - "ollama": Local Ollama
      - "hf":     Hugging Face Inference API / Endpoint
      - "tinyllm": alias for Ollama + tinyllama
      - None: auto -> OpenAI if key set; else HF if HF_TOKEN set; else Ollama
    """
    p = (provider or "").lower()

    if p == "openai":
        return _openai_chat(messages, model or settings.OPENAI_MODEL)
    if p == "hf":
        return _hf_chat(messages, model or os.getenv("HF_MODEL_ID"))
    if p in ("ollama", "tinyllm"):
        forced = "tinyllama" if p == "tinyllm" and not model else model
        return _ollama_chat(messages, forced or settings.OLLAMA_MODEL)

    # auto-detect order: OpenAI -> HF -> Ollama
    if settings.OPENAI_API_KEY:
        return _openai_chat(messages, model or settings.OPENAI_MODEL)
    if os.getenv("HF_TOKEN") and (model or os.getenv("HF_MODEL_ID")):
        return _hf_chat(messages, model or os.getenv("HF_MODEL_ID"))
    return _ollama_chat(messages, model or settings.OLLAMA_MODEL)
