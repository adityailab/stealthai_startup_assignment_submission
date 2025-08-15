from pathlib import Path
import chromadb
from chromadb.config import Settings

PERSIST_DIR = Path("vectorstore")
PERSIST_DIR.mkdir(exist_ok=True)

_client = chromadb.Client(Settings(
    is_persistent=True,
    persist_directory=str(PERSIST_DIR)
))

def get_collection():
    # single collection; we scope by user_id in metadata
    return _client.get_or_create_collection(
        name="bk_chunks",
        metadata={"hnsw:space": "cosine"},
    )
