import os
from sqlalchemy import URL
from dotenv import load_dotenv
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine

load_dotenv()


database_url = URL.create(
    drivername="mysql+aiomysql",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    port=int(os.environ["DB_PORT"]),
    database=os.environ["DB_NAME"],
)

engine = create_async_engine(
    database_url,
    pool_pre_ping=True,
)

sessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with sessionLocal() as session:
        yield session
