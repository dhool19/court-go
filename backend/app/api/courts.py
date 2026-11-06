from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import get_db
from models.court_model import Court
from schemas.court_schema import CourtCreate, CourtResponse, CourtUpdate

router = APIRouter(prefix="/courts", tags=["Courts"])


@router.post("", response_model=CourtResponse, status_code=201)
async def create_court(
    data: CourtCreate,
    db: AsyncSession = Depends(get_db),
):
    court = Court(**data.model_dump())
    db.add(court)
    await db.commit()
    await db.refresh(court)
    return court


@router.get("", response_model=list[CourtResponse])
async def list_courts(db: AsyncSession = Depends(get_db)):
    query = select(Court).order_by(Court.id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{court_id}", response_model=CourtResponse)
async def read_court(
    court_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Court).where(Court.id == court_id))
    db_item = result.scalar_one_or_none()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Court not found")
    return db_item


@router.delete("/{court_id}")
async def delete_court(
    court_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Court).where(Court.id == court_id))
    db_item = result.scalar_one_or_none()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Court not found")
    await db.delete(db_item)
    await db.commit()
    return {"message": "court deleted"}


@router.patch("/{court_id}", response_model=CourtResponse)
async def update_court(
    court_id: int, court_u: CourtUpdate, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Court).where(Court.id == court_id))
    db_item = result.scalar_one_or_none()
    if db_item is None:
        raise HTTPException(status_code=404, detail="Court not found")
    update_data = court_u.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_item, key, value)

    await db.commit()
    await db.refresh(db_item)
    return db_item
