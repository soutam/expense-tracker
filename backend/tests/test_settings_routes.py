import pytest
from httpx import AsyncClient

REGISTER_PAYLOAD = {
    "step1": {
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice@example.com",
        "password": "SecurePass1!",
        "confirm_password": "SecurePass1!",
    },
    "step2": {
        "member1_display_name": "Alice",
        "member2_display_name": "Bob",
        "currency": "USD",
    },
}


async def _register_and_authenticate(client: AsyncClient) -> None:
    """Register a user and leave auth cookies set on the client."""
    response = await client.post("/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 201


# ---------------------------------------------------------------------------
# GET /settings/household
# ---------------------------------------------------------------------------

async def test_get_household_returns_member_names(client: AsyncClient):
    await _register_and_authenticate(client)
    response = await client.get("/settings/household")

    assert response.status_code == 200
    data = response.json()
    assert data["member1_name"] == "Alice"
    assert data["member2_name"] == "Bob"
    assert data["currency"] == "USD"
    assert "id" in data


async def test_get_household_401_when_unauthenticated(client: AsyncClient):
    response = await client.get("/settings/household")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# PUT /settings/household/members
# ---------------------------------------------------------------------------

async def test_update_member_names_returns_new_names(client: AsyncClient):
    await _register_and_authenticate(client)
    response = await client.put(
        "/settings/household/members",
        json={"member1_name": "Husband", "member2_name": "Wife"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["member1_name"] == "Husband"
    assert data["member2_name"] == "Wife"


async def test_update_member_names_persists_across_requests(client: AsyncClient):
    await _register_and_authenticate(client)
    await client.put(
        "/settings/household/members",
        json={"member1_name": "Husband", "member2_name": "Wife"},
    )
    response = await client.get("/settings/household")
    data = response.json()
    assert data["member1_name"] == "Husband"
    assert data["member2_name"] == "Wife"


async def test_update_member_names_clears_member2(client: AsyncClient):
    await _register_and_authenticate(client)
    response = await client.put(
        "/settings/household/members",
        json={"member1_name": "Solo"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["member1_name"] == "Solo"
    assert data["member2_name"] is None


async def test_update_member_names_401_when_unauthenticated(client: AsyncClient):
    response = await client.put(
        "/settings/household/members",
        json={"member1_name": "X"},
    )
    assert response.status_code == 401


async def test_update_member_names_422_on_empty_name(client: AsyncClient):
    await _register_and_authenticate(client)
    response = await client.put(
        "/settings/household/members",
        json={"member1_name": ""},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /settings/categories
# ---------------------------------------------------------------------------

async def test_list_categories_returns_defaults(client: AsyncClient):
    await _register_and_authenticate(client)
    response = await client.get("/settings/categories")

    assert response.status_code == 200
    categories = response.json()
    names = [c["name"] for c in categories]
    assert "Groceries" in names
    assert "Other" in names
    assert len(categories) == 12
    for c in categories:
        assert c["is_default"] is True


async def test_list_categories_401_when_unauthenticated(client: AsyncClient):
    response = await client.get("/settings/categories")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# POST /settings/categories
# ---------------------------------------------------------------------------

async def test_create_category_returns_201(client: AsyncClient):
    await _register_and_authenticate(client)
    response = await client.post("/settings/categories", json={"name": "Pets"})

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Pets"
    assert data["is_default"] is False
    assert "id" in data


async def test_create_category_appears_in_list(client: AsyncClient):
    await _register_and_authenticate(client)
    await client.post("/settings/categories", json={"name": "Pets"})
    response = await client.get("/settings/categories")
    names = [c["name"] for c in response.json()]
    assert "Pets" in names


async def test_create_category_409_on_duplicate_name(client: AsyncClient):
    await _register_and_authenticate(client)
    await client.post("/settings/categories", json={"name": "Pets"})
    response = await client.post("/settings/categories", json={"name": "Pets"})
    assert response.status_code == 409


async def test_create_category_409_on_case_insensitive_duplicate(client: AsyncClient):
    await _register_and_authenticate(client)
    await client.post("/settings/categories", json={"name": "Pets"})
    response = await client.post("/settings/categories", json={"name": "pets"})
    assert response.status_code == 409


async def test_create_category_401_when_unauthenticated(client: AsyncClient):
    response = await client.post("/settings/categories", json={"name": "Pets"})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# PUT /settings/categories/{id}
# ---------------------------------------------------------------------------

async def test_rename_category_returns_new_name(client: AsyncClient):
    await _register_and_authenticate(client)
    create_resp = await client.post("/settings/categories", json={"name": "Pets"})
    category_id = create_resp.json()["id"]

    response = await client.put(f"/settings/categories/{category_id}", json={"name": "Animals"})
    assert response.status_code == 200
    assert response.json()["name"] == "Animals"


async def test_rename_default_category_succeeds(client: AsyncClient):
    await _register_and_authenticate(client)
    list_resp = await client.get("/settings/categories")
    grocery = next(c for c in list_resp.json() if c["name"] == "Groceries")

    response = await client.put(
        f"/settings/categories/{grocery['id']}", json={"name": "Food & Drink"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Food & Drink"


async def test_rename_category_409_on_duplicate(client: AsyncClient):
    await _register_and_authenticate(client)
    r1 = await client.post("/settings/categories", json={"name": "Pets"})
    r2 = await client.post("/settings/categories", json={"name": "Hobbies"})
    hobby_id = r2.json()["id"]

    response = await client.put(f"/settings/categories/{hobby_id}", json={"name": "Pets"})
    assert response.status_code == 409


async def test_rename_category_404_on_unknown_id(client: AsyncClient):
    await _register_and_authenticate(client)
    import uuid
    fake_id = str(uuid.uuid4())
    response = await client.put(f"/settings/categories/{fake_id}", json={"name": "X"})
    assert response.status_code == 404


async def test_rename_category_401_when_unauthenticated(client: AsyncClient):
    import uuid
    response = await client.put(f"/settings/categories/{uuid.uuid4()}", json={"name": "X"})
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /settings/categories/{id}/in-use
# ---------------------------------------------------------------------------

async def test_category_in_use_returns_false_for_new_category(client: AsyncClient):
    await _register_and_authenticate(client)
    create_resp = await client.post("/settings/categories", json={"name": "Pets"})
    category_id = create_resp.json()["id"]

    response = await client.get(f"/settings/categories/{category_id}/in-use")
    assert response.status_code == 200
    data = response.json()
    assert data["in_use"] is False
    assert data["transaction_count"] == 0


async def test_category_in_use_404_on_unknown_id(client: AsyncClient):
    await _register_and_authenticate(client)
    import uuid
    response = await client.get(f"/settings/categories/{uuid.uuid4()}/in-use")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /settings/categories/{id}
# ---------------------------------------------------------------------------

async def test_delete_custom_category_returns_204(client: AsyncClient):
    await _register_and_authenticate(client)
    create_resp = await client.post("/settings/categories", json={"name": "Pets"})
    category_id = create_resp.json()["id"]

    response = await client.delete(f"/settings/categories/{category_id}")
    assert response.status_code == 204


async def test_delete_custom_category_removed_from_list(client: AsyncClient):
    await _register_and_authenticate(client)
    await client.post("/settings/categories", json={"name": "Pets"})
    list_resp = await client.get("/settings/categories")
    pet_cat = next(c for c in list_resp.json() if c["name"] == "Pets")

    await client.delete(f"/settings/categories/{pet_cat['id']}")
    list_resp2 = await client.get("/settings/categories")
    names = [c["name"] for c in list_resp2.json()]
    assert "Pets" not in names


async def test_delete_default_category_returns_400(client: AsyncClient):
    await _register_and_authenticate(client)
    list_resp = await client.get("/settings/categories")
    grocery = next(c for c in list_resp.json() if c["name"] == "Groceries")

    response = await client.delete(f"/settings/categories/{grocery['id']}")
    assert response.status_code == 400


async def test_delete_category_404_on_unknown_id(client: AsyncClient):
    await _register_and_authenticate(client)
    import uuid
    response = await client.delete(f"/settings/categories/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_delete_category_401_when_unauthenticated(client: AsyncClient):
    import uuid
    response = await client.delete(f"/settings/categories/{uuid.uuid4()}")
    assert response.status_code == 401
