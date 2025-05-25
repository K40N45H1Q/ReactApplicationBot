from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

DATABASE_URL = "sqlite+aiosqlite:///./database.db"

engine = create_async_engine(DATABASE_URL, echo=False)
session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)