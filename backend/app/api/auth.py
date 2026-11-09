from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from models.user_model import User
from schemas.user_schema import UserCreate, UserResponse, UserLogin
from db.database import get_db
from core.security import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register_url(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    email = str(data.email).lower()
    result = await db.execute(select(User).where(User.email == email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        )

    password_hash = await run_in_threadpool(hash_password, data.password)

    user = User(
        first_name=data.first_name,
        last_name=data.last_name,
        email=data.email,
        password_hash=password_hash,
        role="client",
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()

        if e.orig.args[0] == 1062:
            raise HTTPException(status_code=409, detail="Email alreday exists") from e
        raise
    await db.refresh(user)
    return user


@router.post("/login", response_model=UserResponse)
async def login_user(
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    email = str(data.email).lower()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    password_is_valid = await run_in_threadpool(
        verify_password,
        data.password,
        user.password_hash,
    )

    if not password_is_valid:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is not active")

    return user
