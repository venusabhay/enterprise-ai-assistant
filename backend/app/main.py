from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.ingest import router as ingest_router
from app.api.health import router as health_router


app = FastAPI(title="Enterprise AI Assistant")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/chat")
app.include_router(ingest_router, prefix="/ingest")
app.include_router(health_router, prefix="/health")