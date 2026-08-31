from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.agent import router as agent_router
from app.api.middleware import RequestTracingMiddleware
from app.core.config import settings
from app.db.database import SessionLocal, init_db
from app.db.seed import seed_demo_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_demo_user(db)
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestTracingMiddleware)

app.include_router(agent_router, prefix="/api/v1")


@app.get("/api/v1/health")
def health():
    return {"status": "ok", "app_name": settings.app_name, "environment": settings.environment}
