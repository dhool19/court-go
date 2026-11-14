from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware

from db.database import Base, engine
from models.user_model import User
from models.slot_model import CourtSlot
from api.courts import router as courts_router
from api.auth import router as users_router
from api.slots import router as slots_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
    allow_origins=["*"],
)

app.include_router(courts_router)
app.include_router(users_router)
app.include_router(slots_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-check")
async def db_check():
    async with engine.connect() as connection:
        result = (await connection.execute(text("SELECT 1"))).scalar_one()
    return {"mysql_connected": result == 1}
