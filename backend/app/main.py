from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text

from db.database import Base, engine
from api.courts import router as courts_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(courts_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-check")
async def db_check():
    async with engine.connect() as connection:
        result = (await connection.execute(text("SELECT 1"))).scalar_one()
    return {"mysql_connected": result == 1}
