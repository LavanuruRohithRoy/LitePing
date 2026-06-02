from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from api.config import settings

# Instantiate non-blocking connection pool to target database engine
engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)

# Generate isolated transaction context session factories
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    """Base paradigm class for declarative SQLAlchemy data models."""
    pass

async def get_db():
    """FastAPI context dependency yielding isolated non-interlocking database transactions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
