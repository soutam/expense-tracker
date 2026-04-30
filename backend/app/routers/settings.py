import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.settings import (
    CategoryCreate,
    CategoryInUseResponse,
    CategoryOut,
    CategoryRename,
    HouseholdMemberNamesUpdate,
    HouseholdOut,
)
from app.services import settings_service

router = APIRouter()


@router.get("/household", response_model=HouseholdOut)
async def get_household(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HouseholdOut:
    household = await settings_service.get_household(current_user.id, db)
    return HouseholdOut.model_validate(household)


@router.put("/household/members", response_model=HouseholdOut)
async def update_member_names(
    body: HouseholdMemberNamesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HouseholdOut:
    household = await settings_service.get_household(current_user.id, db)
    updated = await settings_service.update_member_names(
        household, body.member1_name, body.member2_name, db
    )
    return HouseholdOut.model_validate(updated)


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CategoryOut]:
    household = await settings_service.get_household(current_user.id, db)
    categories = await settings_service.get_categories(household.id, db)
    return [CategoryOut.model_validate(c) for c in categories]


@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    body: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CategoryOut:
    household = await settings_service.get_household(current_user.id, db)
    category = await settings_service.create_category(household.id, body.name, db)
    return CategoryOut.model_validate(category)


@router.get("/categories/{category_id}/in-use", response_model=CategoryInUseResponse)
async def category_in_use(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CategoryInUseResponse:
    household = await settings_service.get_household(current_user.id, db)
    # Verify the category belongs to this household before reporting usage
    categories = await settings_service.get_categories(household.id, db)
    if not any(c.id == category_id for c in categories):
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    count = await settings_service.check_category_in_use(category_id, db)
    return CategoryInUseResponse(in_use=count > 0, transaction_count=count)


@router.put("/categories/{category_id}", response_model=CategoryOut)
async def rename_category(
    category_id: uuid.UUID,
    body: CategoryRename,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CategoryOut:
    household = await settings_service.get_household(current_user.id, db)
    category = await settings_service.rename_category(category_id, household.id, body.name, db)
    return CategoryOut.model_validate(category)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    household = await settings_service.get_household(current_user.id, db)
    await settings_service.delete_category(category_id, household.id, db)
