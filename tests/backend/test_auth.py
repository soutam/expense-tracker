import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.category import Category
from app.models.household import Household
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.auth_service import DEFAULT_CATEGORIES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _register(client: AsyncClient, payload: dict) -> dict:
    return await client.post("/auth/register", json=payload)


async def _login(
    client: AsyncClient,
    email: str = "alice@example.com",
    password: str = "SecurePass1!",
):
    return await client.post("/auth/login", json={"email": email, "password": password})


# ---------------------------------------------------------------------------
# Test 1: Successful registration creates user + household + 12 categories
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_creates_user_household_and_categories(
    client: AsyncClient, register_payload: dict, db_session_factory: async_sessionmaker
):
    resp = await _register(client, register_payload)

    assert resp.status_code == 201
    body = resp.json()
    assert "id" in body
    assert body["email"] == "alice@example.com"

    async with db_session_factory() as db:
        user_count = await db.scalar(select(func.count()).select_from(User))
        household_count = await db.scalar(select(func.count()).select_from(Household))
        category_count = await db.scalar(select(func.count()).select_from(Category))

    assert user_count == 1
    assert household_count == 1
    assert category_count == len(DEFAULT_CATEGORIES)


# ---------------------------------------------------------------------------
# Test 2: Duplicate email registration returns 409
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(
    client: AsyncClient, register_payload: dict, db_session_factory: async_sessionmaker
):
    await _register(client, register_payload)
    resp = await _register(client, register_payload)

    assert resp.status_code == 409
    assert "already registered" in resp.json()["detail"].lower()

    async with db_session_factory() as db:
        user_count = await db.scalar(select(func.count()).select_from(User))
    assert user_count == 1


# ---------------------------------------------------------------------------
# Test 3: Login with valid credentials sets HTTP-only cookies
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_valid_credentials_sets_httponly_cookies(
    client: AsyncClient, register_payload: dict
):
    await _register(client, register_payload)
    resp = await _login(client)

    assert resp.status_code == 200

    set_cookie_headers = resp.headers.get_list("set-cookie")
    cookie_names = [h.split("=")[0].strip() for h in set_cookie_headers]
    assert "access_token" in cookie_names
    assert "refresh_token" in cookie_names

    for header in set_cookie_headers:
        assert "httponly" in header.lower(), f"HttpOnly flag missing in: {header}"


# ---------------------------------------------------------------------------
# Test 4a: Login with wrong password returns 401 with generic message
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_wrong_password_returns_401_generic_message(
    client: AsyncClient, register_payload: dict
):
    await _register(client, register_payload)
    resp = await client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "WrongPassword1!"},
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid credentials"


# ---------------------------------------------------------------------------
# Test 4b: Login with non-existent email returns same 401 (no username hint)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_nonexistent_email_returns_same_401(client: AsyncClient):
    resp = await client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "SomePassword1!"},
    )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid credentials"


# ---------------------------------------------------------------------------
# Test 5: Accessing protected endpoint without token returns 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_me_without_token_returns_401(client: AsyncClient):
    resp = await client.get("/auth/me")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Test 6: Accessing protected endpoint with valid token returns 200
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_me_with_valid_token_returns_user(
    client: AsyncClient, register_payload: dict
):
    await _register(client, register_payload)
    await _login(client)

    resp = await client.get("/auth/me")

    assert resp.status_code == 200
    body = resp.json()
    assert "id" in body
    assert body["email"] == "alice@example.com"


# ---------------------------------------------------------------------------
# Test 7: Logout clears cookies and revokes refresh token
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_logout_clears_cookies_and_revokes_token(
    client: AsyncClient, register_payload: dict, db_session_factory: async_sessionmaker
):
    await _register(client, register_payload)
    login_resp = await _login(client)

    # Capture the refresh token cookie value before logout
    refresh_token_value = client.cookies.get("refresh_token")
    assert refresh_token_value is not None

    logout_resp = await client.post("/auth/logout")
    assert logout_resp.status_code == 204

    # Cookies should be cleared in the response
    set_cookie_headers = logout_resp.headers.get_list("set-cookie")
    assert len(set_cookie_headers) > 0, "Expected Set-Cookie headers to clear cookies"
    for header in set_cookie_headers:
        assert "max-age=0" in header.lower() or "expires=" in header.lower(), (
            f"Cookie should be cleared but got: {header}"
        )

    # The specific refresh token used in this session must be revoked in the DB
    import hashlib
    expected_hash = hashlib.sha256(refresh_token_value.encode()).hexdigest()
    async with db_session_factory() as db:
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == expected_hash)
        )
        token = result.scalar_one_or_none()
    assert token is not None, "Refresh token should exist in DB"
    assert token.revoked, "Active refresh token should be revoked after logout"

    # A subsequent refresh attempt must fail
    refresh_resp = await client.post("/auth/refresh")
    assert refresh_resp.status_code == 401


# ---------------------------------------------------------------------------
# Test 8: Refresh token generates a new access token
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_refresh_issues_new_access_token(
    client: AsyncClient, register_payload: dict
):
    await _register(client, register_payload)
    await _login(client)

    original_access_token = client.cookies.get("access_token")
    assert original_access_token is not None

    refresh_resp = await client.post("/auth/refresh")
    assert refresh_resp.status_code == 200

    new_access_token = client.cookies.get("access_token")
    assert new_access_token is not None
    assert new_access_token != original_access_token
