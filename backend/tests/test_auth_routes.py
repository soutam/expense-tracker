import pytest
from httpx import AsyncClient

REGISTER_PAYLOAD = {
    "step1": {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane@example.com",
        "password": "SecurePass1!",
        "confirm_password": "SecurePass1!",
    },
    "step2": {
        "member1_display_name": "Janie",
        "currency": "USD",
    },
}


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------

async def test_register_returns_201_with_user_fields(client: AsyncClient):
    response = await client.post("/auth/register", json=REGISTER_PAYLOAD)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "jane@example.com"
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Smith"
    assert "id" in data


async def test_register_sets_http_only_auth_cookies(client: AsyncClient):
    response = await client.post("/auth/register", json=REGISTER_PAYLOAD)

    assert response.status_code == 201
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


async def test_register_409_on_duplicate_email(client: AsyncClient):
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    response = await client.post("/auth/register", json=REGISTER_PAYLOAD)

    assert response.status_code == 409


async def test_register_422_on_mismatched_passwords(client: AsyncClient):
    payload = {
        **REGISTER_PAYLOAD,
        "step1": {**REGISTER_PAYLOAD["step1"], "confirm_password": "DifferentPass1!"},
    }
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 422


async def test_register_422_on_short_password(client: AsyncClient):
    payload = {
        **REGISTER_PAYLOAD,
        "step1": {
            **REGISTER_PAYLOAD["step1"],
            "email": "other@example.com",
            "password": "short",
            "confirm_password": "short",
        },
    }
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 422


async def test_register_422_on_invalid_email(client: AsyncClient):
    payload = {
        **REGISTER_PAYLOAD,
        "step1": {**REGISTER_PAYLOAD["step1"], "email": "not-an-email"},
    }
    response = await client.post("/auth/register", json=payload)
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

async def test_login_200_with_valid_credentials(client: AsyncClient):
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    # Clear cookies so login starts fresh
    client.cookies.clear()

    response = await client.post(
        "/auth/login",
        json={"email": "jane@example.com", "password": "SecurePass1!"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "jane@example.com"
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


async def test_login_401_on_wrong_password(client: AsyncClient):
    await client.post("/auth/register", json=REGISTER_PAYLOAD)

    response = await client.post(
        "/auth/login",
        json={"email": "jane@example.com", "password": "WrongPassword!"},
    )
    assert response.status_code == 401


async def test_login_401_on_nonexistent_email(client: AsyncClient):
    response = await client.post(
        "/auth/login",
        json={"email": "ghost@example.com", "password": "Password123!"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------

async def test_me_200_returns_user_when_authenticated(client: AsyncClient):
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    # Cookie persists in the same client instance
    response = await client.get("/auth/me")

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "jane@example.com"
    assert data["first_name"] == "Jane"
    assert data["last_name"] == "Smith"


async def test_me_401_without_cookie(client: AsyncClient):
    response = await client.get("/auth/me")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------

async def test_logout_204_and_subsequent_me_is_401(client: AsyncClient):
    await client.post("/auth/register", json=REGISTER_PAYLOAD)

    logout_response = await client.post("/auth/logout")
    assert logout_response.status_code == 204

    me_response = await client.get("/auth/me")
    assert me_response.status_code == 401


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------

async def test_refresh_200_issues_new_tokens(client: AsyncClient):
    await client.post("/auth/register", json=REGISTER_PAYLOAD)

    response = await client.post("/auth/refresh")

    assert response.status_code == 200
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


async def test_refresh_401_without_cookie(client: AsyncClient):
    response = await client.post("/auth/refresh")
    assert response.status_code == 401


async def test_refresh_401_after_logout(client: AsyncClient):
    await client.post("/auth/register", json=REGISTER_PAYLOAD)
    await client.post("/auth/logout")

    response = await client.post("/auth/refresh")
    assert response.status_code == 401
