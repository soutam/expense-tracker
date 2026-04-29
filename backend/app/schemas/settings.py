import uuid

from pydantic import BaseModel, ConfigDict, Field


class HouseholdMemberNamesUpdate(BaseModel):
    member1_name: str = Field(min_length=1, max_length=100)
    member2_name: str | None = Field(default=None, max_length=100)


class HouseholdOut(BaseModel):
    id: uuid.UUID
    member1_name: str
    member2_name: str | None
    currency: str

    model_config = ConfigDict(from_attributes=True)


class CategoryOut(BaseModel):
    id: uuid.UUID
    name: str
    is_default: bool

    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CategoryRename(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CategoryInUseResponse(BaseModel):
    in_use: bool
    transaction_count: int
