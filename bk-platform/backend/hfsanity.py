# hf_sanity.py
import os, httpx
from app.core.config import settings

print("HF_TOKEN present:", bool(settings.HF_TOKEN), "(masked:", (settings.HF_TOKEN[:6] + "..." if settings.HF_TOKEN else None), ")")
print("HF_MODEL_ID:", settings.HF_MODEL_ID)
print("HF_API_BASE:", settings.HF_API_BASE)

headers = {"Authorization": f"Bearer {settings.HF_TOKEN}"}

# 1) whoami
resp = httpx.get("https://huggingface.co/api/whoami-v2", headers=headers, timeout=30)
print("whoami:", resp.status_code, resp.text[:200])

# 2) tiny inference
url = f"{settings.HF_API_BASE.rstrip('/')}/{settings.HF_MODEL_ID}"
payload = {
  "inputs": "Say 'hello' in one word.",
  "parameters": {"max_new_tokens": 8}
}
resp2 = httpx.post(url, headers=headers, json=payload, timeout=60)
print("inference:", resp2.status_code, resp2.text[:300])
