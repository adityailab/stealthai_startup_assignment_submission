# hf_diag.py
# pip install requests python-dotenv
import os
import sys
import json
import argparse
import requests
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()  # load .env if present
except Exception:
    pass

HF_TOKEN = os.getenv("HF_TOKEN", "").strip()
DEFAULT_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"

API_WHOAMI = "https://huggingface.co/api/whoami-v2"
API_MODEL   = "https://huggingface.co/api/models/{repo_id}"
API_INFER   = "https://api-inference.huggingface.co/models/{repo_id}"

def pretty(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False)

def fail(msg, extra=None, code=1):
    print(f"\n❌ {msg}")
    if extra:
        print(extra if isinstance(extra, str) else pretty(extra))
    sys.exit(code)

def warn(msg):
    print(f"\n⚠️  {msg}")

def ok(msg):
    print(f"\n✅ {msg}")

def check_token(token: str):
    print("=== 1) Checking HF token presence & format ===")
    if not token:
        fail("HF_TOKEN is not set. Put it in your .env as HF_TOKEN=hf_... or export it before running.")
    print(f"HF_TOKEN starts with 'hf_': {token.startswith('hf_')}")
    if not token.startswith("hf_"):
        warn("Token does not start with 'hf_'. Are you sure you copied the secret token (not the name/ID)?")
    # Ping whoami
    print("\n→ Calling whoami to validate token…")
    r = requests.get(API_WHOAMI, headers={"Authorization": f"Bearer {token}"})
    if r.status_code == 200:
        data = r.json()
        ok("Token is valid.")
        print("Account:", data.get("name"), "| Org memberships:", [o.get("name") for o in data.get("orgs", [])])
    elif r.status_code == 401:
        fail("Token invalid (401 Unauthorized). Regenerate a new Read token and paste it into .env.")
    else:
        warn(f"Unexpected whoami status: {r.status_code}\n{r.text[:300]}")

def check_model_access(token: str, repo_id: str):
    print("\n=== 2) Checking model card API (gated / existence / access) ===")
    url = API_MODEL.format(repo_id=repo_id)
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"})
    if r.status_code == 200:
        data = r.json()
        gated = data.get("gated")
        private = data.get("private")
        disabled = data.get("disabled")
        ok(f"Model '{repo_id}' is visible to your token.")
        print("gated:", gated, "| private:", private, "| disabled:", disabled)
        if gated:
            warn("This model is gated. You must click 'Agree and access' on the model page before inference will work:\n"
                 f"  https://huggingface.co/{repo_id}")
        return True
    elif r.status_code == 404:
        fail(f"Model '{repo_id}' not found (404). Check HF_MODEL_ID / spelling.")
    elif r.status_code == 403:
        fail(f"Access denied to '{repo_id}' (403). You likely haven't accepted the license yet:\n  https://huggingface.co/{repo_id}")
    elif r.status_code == 401:
        fail("401 Unauthorized while fetching model card. Token is not valid for API calls.")
    else:
        fail(f"Unexpected status {r.status_code} from model card API.", r.text[:300])

def tiny_inference(token: str, repo_id: str):
    print("\n=== 3) Performing a tiny inference call ===")
    url = API_INFER.format(repo_id=repo_id)
    payload = {"inputs": "Hello from a diagnostic script."}
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    r = requests.post(url, headers=headers, json=payload)
    print("Status:", r.status_code)
    if r.status_code == 200:
        try:
            data = r.json()
            ok("Inference API call succeeded.")
            print(pretty(data)[:1200])
        except Exception:
            ok("Inference API call succeeded (non-JSON).")
            print(r.text[:1200])
        return
    elif r.status_code == 503:
        warn("Model is loading (503). This is normal on serverless; try again in ~10–60s.")
        print(r.text[:300])
        return
    elif r.status_code == 401:
        fail("401 Unauthorized on inference. Token invalid OR license not accepted for this model.", r.text[:300])
    elif r.status_code == 403:
        fail("403 Forbidden on inference. You probably need to accept the license for this model.", r.text[:300])
    elif r.status_code == 404:
        fail("404 from inference endpoint. Repo id may be wrong.", r.text[:300])
    else:
        fail(f"Unexpected status {r.status_code} from inference API.", r.text[:300])

def main():
    parser = argparse.ArgumentParser(description="Hugging Face token & model access diagnostic")
    parser.add_argument("--model", default=os.getenv("HF_MODEL_ID") or DEFAULT_MODEL,
                        help="Model repo id (e.g. mistralai/Mistral-7B-Instruct-v0.2)")
    args = parser.parse_args()

    # Print what we are using
    print("Env file present?:", Path(".env").exists())
    print("Using MODEL:", args.model)

    check_token(HF_TOKEN)
    check_model_access(HF_TOKEN, args.model)
    tiny_inference(HF_TOKEN, args.model)
    ok("All checks done.")

if __name__ == "__main__":
    main()
