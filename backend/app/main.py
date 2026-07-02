import logging
from contextlib import asynccontextmanager
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import ENV_FILE, settings
from app.core.database import Base, engine
from app.routers import auth, acts, clients, contracts, dashboard, documents, invoices, payments
from app.routers import settings as settings_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        parsed = urlparse(settings.DATABASE_URL.replace("+asyncpg", ""))
        logger.error(
            "Не удалось подключиться к PostgreSQL: %s@%s:%s/%s. "
            "Проверьте backend/.env (файл: %s).",
            parsed.username,
            parsed.hostname,
            parsed.port,
            parsed.path.lstrip("/"),
            ENV_FILE,
        )
        raise RuntimeError(
            f"Ошибка подключения к БД. Отредактируйте {ENV_FILE} — "
            f"укажите верный DATABASE_URL (сейчас user={parsed.username}). "
            f"Оригинал: {e}"
        ) from e
    yield


app = FastAPI(title="CRM API", version="1.0.0", lifespan=lifespan)

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(clients.router, prefix="/api")
app.include_router(contracts.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(invoices.router, prefix="/api")
app.include_router(acts.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(settings_router.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
