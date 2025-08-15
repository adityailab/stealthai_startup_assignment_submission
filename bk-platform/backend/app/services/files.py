from pathlib import Path
from typing import Tuple
from fastapi import UploadFile, HTTPException

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_BYTES = 100 * 1024 * 1024  # 100MB

def _read_all(file: UploadFile) -> bytes:
    data = file.file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large (limit 100MB)")
    return data

def save_upload_file(file: UploadFile) -> Tuple[str, int, str, bytes]:
    data = _read_all(file)
    safe_name = file.filename.replace("/", "_")

    dest = UPLOAD_DIR / safe_name
    i = 1
    while dest.exists():
        dest = UPLOAD_DIR / f"{dest.stem}_{i}{dest.suffix}"
        i += 1

    dest.write_bytes(data)
    size = len(data)
    mime = file.content_type or "application/octet-stream"
    return str(dest), size, mime, data
