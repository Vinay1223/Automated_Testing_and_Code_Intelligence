"""SQLAlchemy engine + session factory.

We use the 2.x async-ready core. The API hands a session to the repository
classes — none of the route handlers reach into SQLAlchemy directly.
"""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker


@lru_cache(maxsize=1)
def get_engine(url: str) -> Engine:
    return create_engine(url, pool_pre_ping=True, future=True)


@lru_cache(maxsize=1)
def get_sessionmaker(url: str):
    return sessionmaker(bind=get_engine(url), autoflush=False, expire_on_commit=False, future=True)
