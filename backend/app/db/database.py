from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings

_raw_url = settings.database_url
# Neon/Vercel Postgres often hand out "postgres://" URLs; SQLAlchemy's
# dialect resolution requires the "postgresql://" scheme.
if _raw_url.startswith("postgres://"):
    _raw_url = _raw_url.replace("postgres://", "postgresql://", 1)

_is_sqlite = "sqlite" in _raw_url
connect_args = {"check_same_thread": False} if _is_sqlite else {}

# In a serverless environment (Vercel Functions), each cold start gets its
# own process — SQLAlchemy's default connection pool doesn't help across
# invocations and can even exhaust the DB's connection limit. NullPool
# opens a fresh connection per request and lets Neon's own pooler (if the
# connection string points at one) handle real pooling upstream.
engine_kwargs = {} if _is_sqlite else {"poolclass": NullPool}

engine = create_engine(_raw_url, connect_args=connect_args, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.db import models  # noqa: F401  (register models on Base)

    Base.metadata.create_all(bind=engine)

