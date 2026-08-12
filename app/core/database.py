from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config.settings import settings


# This manages the connection pool to your PostgreSQL Docker container.
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # Prints SQL queries to the console in dev mode
    pool_pre_ping=True,  # Automatically reconnects if the DB drops the connection
)

# This creates temporary sessions for each API request or background task.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevents lazy-loading errors after a commit
)


# All future SQLAlchemy models (User, Insight, etc.) will inherit from this.
class Base(DeclarativeBase):
    pass


# This function is injected into your API routes. It opens a session,
# yields it to the route, and then automatically commits or rolls back.
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
