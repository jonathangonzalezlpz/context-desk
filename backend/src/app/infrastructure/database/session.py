from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.src.app.core.config import settings

# Fast and async PostgreSQL connection using asyncpg (Requires psycopg changed to asyncpg or using async psycopg)
# The pyproject has psycopg2-binary, indicating sync engine, but standard modern fastapi uses async.
# We'll use standard sync for simplicity as defined in pyproject, or adjust to async.
# The user asked for clean code and professional setup. Let's use psycopg3 or sqlalchemy async if possible.
# For now, sticking to sync SQLAlchemy with standard psycopg2.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
