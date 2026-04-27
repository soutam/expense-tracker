import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CredentialsException, EmailAlreadyRegisteredException
from app.core.security import hash_password, verify_password
from app.models.category import Category
from app.models.household import Household
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.services import token_service

DEFAULT_CATEGORIES = [
    "Groceries",
    "Dining Out",
    "Utilities",
    "Rent/Mortgage",
    "Transportation",
    "Entertainment",
    "Healthcare",
    "Clothing",
    "Personal Care",
    "Education",
    "Travel",
    "Miscellaneous",
]

# Pre-hashed dummy used to keep response time constant regardless of whether email exists
_DUMMY_HASH = hash_password("dummy-value-timing-attack-prevention")


async def register_user(db: AsyncSession, request: RegisterRequest) -> User:
    result = await db.execute(select(User).where(User.email == request.step1.email))
    if result.scalar_one_or_none() is not None:
        raise EmailAlreadyRegisteredException()

    user = User(
        email=request.step1.email,
        password_hash=hash_password(request.step1.password),
    )
    db.add(user)
    await db.flush()  # get user.id without committing

    household = Household(
        member1_id=user.id,
        member1_name=request.step2.member1_display_name,
        member2_name=request.step2.member2_display_name,
        currency=request.step2.currency,
    )
    db.add(household)
    await db.flush()  # get household.id

    categories = [
        Category(household_id=household.id, name=name, is_default=True)
        for name in DEFAULT_CATEGORIES
    ]
    db.add_all(categories)

    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user is None:
        # Constant-time check to prevent timing-based email enumeration
        verify_password(password, _DUMMY_HASH)
        raise CredentialsException()

    if user.password_hash is None or not verify_password(password, user.password_hash):
        raise CredentialsException()

    return user


async def create_and_store_refresh_token(db: AsyncSession, user_id: uuid.UUID) -> str:
    raw, token_hash = token_service.create_refresh_token()
    expires_at = token_service.refresh_token_expires_at()

    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        revoked=False,
    )
    db.add(refresh_token)
    await db.commit()
    return raw


async def logout_user(db: AsyncSession, raw_refresh_token: str) -> None:
    token_hash = token_service.hash_refresh_token(raw_refresh_token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    token = result.scalar_one_or_none()
    if token:
        token.revoked = True
        await db.commit()


async def validate_and_rotate_refresh_token(
    db: AsyncSession, raw_refresh_token: str
) -> tuple[User, str]:
    token_hash = token_service.hash_refresh_token(raw_refresh_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,  # noqa: E712
        )
    )
    stored = result.scalar_one_or_none()

    if stored is None or stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise CredentialsException()

    user_result = await db.execute(select(User).where(User.id == stored.user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise CredentialsException()

    stored.revoked = True
    await db.flush()

    new_raw, new_hash = token_service.create_refresh_token()
    new_token = RefreshToken(
        user_id=user.id,
        token_hash=new_hash,
        expires_at=token_service.refresh_token_expires_at(),
        revoked=False,
    )
    db.add(new_token)
    await db.commit()

    return user, new_raw
