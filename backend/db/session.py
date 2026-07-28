"""
DevVerse AI - Database Configuration

Async database session management with SQLAlchemy 2.0.
Includes connection pooling and transaction handling.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    async_scoped_session,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import NullPool

from core.config import settings


# Create async engine with connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Scoped session for request-level sessions
# Uses asyncio scope for proper async context handling
db_session = async_scoped_session(
    async_session_factory,
    scopefunc=lambda: id(asyncio.current_task()),
)


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    Provides common functionality and metadata.
    """
    
    # Type annotations for better IDE support
    id: Mapped[int] = mapped_column(primary_key=True)
    
    @classmethod
    async def get_all(cls, session: AsyncSession) -> list:
        """Get all records of this model."""
        from sqlalchemy import select
        result = await session.execute(select(cls))
        return list(result.scalars().all())
    
    @classmethod
    async def get_by_id(cls, session: AsyncSession, record_id: int):
        """Get a single record by ID."""
        from sqlalchemy import select
        result = await session.execute(select(cls).where(cls.id == record_id))
        return result.scalar_one_or_none()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database sessions.
    
    Yields:
        AsyncSession: Database session
        
    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.
    
    Note: In production, use Alembic migrations instead.
    This is primarily for development/testing.
    """
    from db.base import Base
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()


# Import asyncio here to avoid circular imports
import asyncio
