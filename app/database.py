"""SQLAlchemy engine, session factory and database initialization."""

import logging
from typing import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_database_url


logger = logging.getLogger("fitbuddy.db")

DATABASE_URL = get_database_url()

connect_args = (
    {"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


@event.listens_for(Engine, "connect")
def _fk(dbapi_connection, connection_record):
    """Enable SQLite foreign-key enforcement."""
    if DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db() -> Iterator[Session]:
    """Provide a database session to FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Import all models and create missing database tables."""
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    logger.info(
        "Database initialized. Tables: %s",
        list(Base.metadata.tables.keys()),
    )
