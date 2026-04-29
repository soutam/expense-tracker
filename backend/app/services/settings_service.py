import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.household import Household


async def get_household(user_id: uuid.UUID, db: AsyncSession) -> Household:
    result = await db.execute(
        select(Household).where(
            (Household.member1_id == user_id) | (Household.member2_id == user_id)
        )
    )
    household = result.scalar_one_or_none()
    if household is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Household not found",
        )
    return household


async def update_member_names(
    household: Household,
    member1_name: str,
    member2_name: str | None,
    db: AsyncSession,
) -> Household:
    household.member1_name = member1_name
    household.member2_name = member2_name
    await db.commit()
    await db.refresh(household)
    return household


async def get_categories(household_id: uuid.UUID, db: AsyncSession) -> list[Category]:
    result = await db.execute(
        select(Category)
        .where(Category.household_id == household_id)
        .order_by(Category.is_default.desc(), Category.name)
    )
    return list(result.scalars().all())


async def create_category(
    household_id: uuid.UUID, name: str, db: AsyncSession
) -> Category:
    existing = await db.execute(
        select(Category).where(
            Category.household_id == household_id,
            func.lower(Category.name) == name.strip().lower(),
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A category with this name already exists",
        )
    category = Category(household_id=household_id, name=name.strip(), is_default=False)
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def rename_category(
    category_id: uuid.UUID,
    household_id: uuid.UUID,
    new_name: str,
    db: AsyncSession,
) -> Category:
    result = await db.execute(
        select(Category).where(
            Category.id == category_id,
            Category.household_id == household_id,
        )
    )
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    duplicate = await db.execute(
        select(Category).where(
            Category.household_id == household_id,
            func.lower(Category.name) == new_name.strip().lower(),
            Category.id != category_id,
        )
    )
    if duplicate.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A category with this name already exists",
        )

    category.name = new_name.strip()
    await db.commit()
    await db.refresh(category)
    return category


async def check_category_in_use(category_id: uuid.UUID, db: AsyncSession) -> int:
    # Placeholder until the Transaction model is created in SCRUM-10.
    # Always returns 0 — no transactions table exists yet.
    return 0


async def delete_category(
    category_id: uuid.UUID, household_id: uuid.UUID, db: AsyncSession
) -> None:
    result = await db.execute(
        select(Category).where(
            Category.id == category_id,
            Category.household_id == household_id,
        )
    )
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    if category.is_default:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Default categories cannot be deleted",
        )
    await db.delete(category)
    await db.commit()
