# 🕵️‍♂️ StealthAI Startup Assignment Submission

This repository contains the full-stack submission for the **StealthAI Startup Assignment**, showcasing an AI-powered Retrieval-Augmented Generation (RAG) application capable of answering domain-specific questions based on uploaded documents (PDFs, images, receipts, etc.).

---

## 🚀 Features

### 🔍 Backend (FastAPI)
- User Authentication (Register/Login)
- Document Upload & Parsing
- Document Chunking + Embedding (ChromaDB)
- Contextual Question Answering using LLMs:
  - 🔁 Ollama (local inference, e.g., `phi3:3.8b`)
  - ☁️ OpenAI (optional)
  - 🤗 HuggingFace Inference API (optional)
- Strict answer mode with citation-based output
- Admin Dashboard API (for managing documents)

### 🧠 LLM & RAG Pipeline
- Converts uploaded files into searchable chunks
- Supports semantic retrieval via vector search
- Provides grounded responses strictly based on retrieved chunks
- Returns relevant citation snippets for transparency

---

## 🖥️ Frontend (optional)
A minimal web UI can be built using [Vite](https://vitejs.dev/) or any React/Vue framework to:
- Upload files
- Ask questions
- Display answers + citations

*(Frontend not included in this submission)*

---

## 📂 Project Structure

```
backend/
├── app/
│   ├── api/           # FastAPI routes
│   ├── core/          # Settings and configuration
│   ├── db/            # SQLAlchemy models
│   ├── models/        # ORM models (e.g., Document)
│   ├── services/      # Embedding, LLM, Auth
│   ├── vector/        # Chroma client
│   └── main.py        # FastAPI entrypoint
├── .env               # Environment variables (HF/Ollama/OpenAI)
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup Instructions

### 🐍 Backend (FastAPI)

#### 1. Clone and setup virtual environment:
```bash
git clone https://github.com/adityailab/stealthai_startup_assignment_submission.git
cd stealthai_startup_assignment_submission/backend

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. Configure `.env`
```ini
APP_NAME="BK Platform"
ENV=dev
SECRET_KEY=your_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DATABASE_URL=sqlite:///./bk.db

# Choose one provider:

# -- Local Ollama --
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=phi3:3.8b

# -- OR Hugging Face (optional) --
# HF_TOKEN=hf_xxx
# HF_MODEL_ID=mistralai/Mistral-7B-Instruct-v0.2
# HF_API_BASE=https://api-inference.huggingface.co/models

# -- OR OpenAI (optional) --
# OPENAI_API_KEY=sk-xxx
# OPENAI_MODEL=gpt-4o
```

#### 3. Run the server:
```bash
uvicorn app.main:app --reload --port 8001
```

#### 4. Access Swagger docs:
> [http://localhost:8001/docs](http://localhost:8001/docs)

---

## 📦 API Endpoints

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET  /api/auth/profile`
- `POST /api/documents/upload` - Upload PDFs/images
- `GET  /api/documents` - List user documents
- `POST /api/knowledge/ask` - Ask a question with `strict=true` and get citations

---

## 🧪 Example Query (Swagger)
```json
{
  "question": "What is the price of Mocha?",
  "k": 6,
  "max_context_tokens": 800,
  "provider": "ollama",
  "model": "phi3:3.8b",
  "strict": true
}
```

---

## 📌 Notes

- Avoid uploading `.venv` or `site-packages` folders (filtered via `.gitignore`)
- Supports citation-based output for transparency
- HF API models must be accessible via token or Inference Endpoint
- Ollama is preferred for offline/local RAG demos

---

## 🧑‍💻 Author

**Aditya Patane**    
[GitHub](https://github.com/adityailab) • [LinkedIn](https://www.linkedin.com/in/adityapatane)

---

## 🛡 License

This project is submitted as part of the StealthAI Startup Assignment.  
Not intended for production use without modifications.
