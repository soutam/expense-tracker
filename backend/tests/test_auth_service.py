from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CredentialsException, EmailAlreadyRegisteredException
from app.models.category import Category
from app.models.household import Household
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import RegisterRequest, RegisterStep1, RegisterStep2
from app.services import auth_service, token_service


def _make_register_request(
    email: str = "test@example.com",
    password: str = "Password123!",
    first_name: str = "John",
    last_name: str = "Doe",
    display_name: str = "Johnny",
    currency: str = "USD",
) -> RegisterRequest:
    return RegisterRequest(
        step1=RegisterStep1(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            confirm_password=password,
        ),
        step2=RegisterStep2(
            member1_display_name=display_name,
            currency=currency,
        ),
    )


# ---------------------------------------------------------------------------
# register_user
# ---------------------------------------------------------------------------

async def test_register_user_persists_email_and_name(db: AsyncSession):
    user = await auth_service.register_user(db, _make_register_request())

    assert user.email == "test@example.com"
    assert user.first_name == "John"
    assert user.last_name == "Doe"


async def test_register_user_hashes_password_not_stored_plaintext(db: AsyncSession):
    user = await auth_service.register_user(db, _make_register_request())

    assert user.password_hash is not None
    assert user.password_hash != "Password123!"


async def test_register_user_creates_household(db: AsyncSession):
    user = await auth_service.register_user(db, _make_register_request())

    result = await db.execute(select(Household).where(Household.member1_id == user.id))
    household = result.scalar_one_or_none()

    assert household is not None
    assert household.member1_name == "Johnny"
    assert household.currency == "USD"
    assert household.member2_id is None


async def test_register_user_creates_twelve_default_categories(db: AsyncSession):
    user = await auth_service.register_user(db, _make_register_request())

    hh_result = await db.execute(select(Household).where(Household.member1_id == user.id))
    household = hh_result.scalar_one()

    cat_result = await db.execute(
        select(Category).where(Category.household_id == household.id)
    )
    categories = cat_result.scalars().all()

    assert len(categories) == 12
    assert all(c.is_default for c in categories)


async def test_register_user_duplicate_email_raises(db: AsyncSession):
    req = _make_register_request()
    await auth_service.register_user(db, req)

    with pytest.raises(EmailAlreadyRegisteredException):
        await auth_service.register_user(db, req)


# ---------------------------------------------------------------------------
# authenticate_user
# ---------------------------------------------------------------------------

async def test_authenticate_user_valid_credentials(db: AsyncSession):
    await auth_service.register_user(db, _make_register_request())

    user = await auth_service.authenticate_user(db, "test@example.com", "Password123!")
    assert user.email == "test@example.com"


async def test_authenticate_user_wrong_password_raises(db: AsyncSession):
    await auth_service.register_user(db, _make_register_request())

    with pytest.raises(CredentialsException):
        await auth_service.authenticate_user(db, "test@example.com", "WrongPassword!")


async def test_authenticate_user_nonexistent_email_raises(db: AsyncSession):
    with pytest.raises(CredentialsException):
        await auth_service.authenticate_user(db, "nobody@example.com", "Password123!")


async def test_authenticate_user_oauth_account_without_password_raises(db: AsyncSession):
    oauth_user = User(
        email="oauth@example.com",
        first_name="OAuth",
        last_name="User",
        password_hash=None,
        oauth_provider="google",
    )
    db.add(oauth_user)
    await db.commit()

    with pytest.raises(CredentialsException):
        await auth_service.authenticate_user(db, "oauth@example.com", "anypassword")


# ---------------------------------------------------------------------------
# create_and_store_refresh_token
# ---------------------------------------------------------------------------

async def test_create_and_store_refresh_token_returns_raw_string(db: AsyncSession):
    user = await auth_service.register_user(db, _make_register_request())

    raw = await auth_service.create_and_store_refresh_token(db, user.id)

    assert isinstance(raw, str) and len(raw) > 0


async def test_create_and_store_refresh_token_stores_hash_not_plaintext(db: AsyncSession):
    user = await auth_service.register_user(db, _make_register_request())
    raw = await auth_service.create_and_store_refresh_token(db, user.id)

    result = await db.execute(select(RefreshToken).where(RefreshToken.user_id == user.id))
    stored = result.scalar_one_or_none()

    assert stored is not None
    assert stored.revoked is False
    assert stored.token_hash != raw  # hash stored, not plaintext


# ---------------------------------------------------------------------------
# logout_user
# ---------------------------------------------------------------------------

async def test_logout_user_revokes_refresh_token(db: AsyncSession):
    user = await auth_service.register_user(db, _make_register_request())
    raw = await auth_service.create_and_store_refresh_token(db, user.id)

    await auth_service.logout_user(db, raw)

    result = await db.execute(select(RefreshToken).where(RefreshToken.user_id == user.id))
    stored = result.scalar_one()
    assert stored.revoked is True


async def test_logout_user_unknown_token_is_noop(db: AsyncSession):
    # Should not raise even when the token doesn't exist
    await auth_service.logout_user(db, "non-existent-token-value")


# ---------------------------------------------------------------------------
# validate_and_rotate_refresh_token
# ---------------------------------------------------------------------------

async def test_validate_and_rotate_returns_user_and_new_token(db: AsyncSession):
    user = await auth_service.register_user(db, _make_register_request())
    raw = await auth_service.create_and_store_refresh_token(db, user.id)

    returned_user, new_raw = await auth_service.validate_and_rotate_refresh_token(db, raw)

    assert returned_user.id == user.id
    assert new_raw != raw


async def test_validate_and_rotate_revokes_old_token(db: AsyncSession):
    user = await auth_service.register_user(db, _make_register_request())
    raw = await auth_service.create_and_store_refresh_token(db, user.id)

    await auth_service.validate_and_rotate_refresh_token(db, raw)

    old_hash = token_service.hash_refresh_token(raw)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == old_hash))
    old_stored = result.scalar_one()
    assert old_stored.revoked is True


async def test_validate_and_rotate_revoked_token_raises(db: AsyncSession):
    user = await auth_service.register_user(db, _make_register_request())
    raw = await auth_service.create_and_store_refresh_token(db, user.id)
    await auth_service.logout_user(db, raw)  # revoke

    with pytest.raises(CredentialsException):
        await auth_service.validate_and_rotate_refresh_token(db, raw)


async def test_validate_and_rotate_expired_token_raises(db: AsyncSession):
    user = await auth_service.register_user(db, _make_register_request())

    raw, token_hash = token_service.create_refresh_token()
    expired = RefreshToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        revoked=False,
    )
    db.add(expired)
    await db.commit()

    with pytest.raises(CredentialsException):
        await auth_service.validate_and_rotate_refresh_token(db, raw)


async def test_validate_and_rotate_nonexistent_token_raises(db: AsyncSession):
    with pytest.raises(CredentialsException):
        await auth_service.validate_and_rotate_refresh_token(db, "fake-token-value")
