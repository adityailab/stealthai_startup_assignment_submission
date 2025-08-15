from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db import init_db
from app.api import auth as auth_router
from app.api import search as search_router
from app.api import documents as documents_router
from app.api import knowledge as knowledge_router


app = FastAPI(
    title=settings.APP_NAME,
    swagger_ui_parameters={"persistAuthorization": True}
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

# Routers
app.include_router(auth_router.router)
app.include_router(documents_router.router)
app.include_router(search_router.router)
app.include_router(knowledge_router.router)



# init tables
init_db()
