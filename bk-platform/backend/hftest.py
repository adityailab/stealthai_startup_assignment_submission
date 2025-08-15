# hf_probe.py
import os, httpx, time
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("HF_TOKEN")
BASE  = (os.getenv("HF_API_BASE") or "https://api-inference.huggingface.co/models").rstrip("/")

candidates = [
    # very likely to work on serverless
    "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "Qwen/Qwen2.5-1.5B-Instruct",
    "Qwen/Qwen2.5-3B-Instruct",
    "meta-llama/Llama-3.2-1B-Instruct",   # small, usually public
    "google/gemma-2-2b-it",               # sometimes 404 depending on region
]

headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type":"application/json"}
payload = {"inputs": "Say 'ready'."}

for repo in candidates:
    url = f"{BASE}/{repo}"
    print(f"\nTrying: {repo}\nPOST {url}")
    try:
        r = httpx.post(url, headers=headers, json=payload, timeout=60)
        print("Status:", r.status_code)
        print("Body  :", (r.text[:300] + ("…" if len(r.text) > 300 else "")))
        if r.status_code in (200, 503):
            print(f"\n>>> USE THIS MODEL: {repo}  (200 OK or 503 loading)")
            break
    except Exception as e:
        print("Error:", e)
