import pytest
from httpx import AsyncClient


async def register_and_login(client: AsyncClient, email: str = "test@example.com") -> str:
    await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test User",
            "email": email,
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    return login_res.json()["access_token"]


@pytest.mark.asyncio
async def test_accounts_and_categories_crud(client: AsyncClient):
    token = await register_and_login(client, "accounts_test@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Categories should be pre-seeded
    cat_res = await client.get("/api/v1/categories", headers=headers)
    assert cat_res.status_code == 200
    categories = cat_res.json()["items"]
    assert len(categories) >= 12  # default expense & income categories

    # 2. Create custom category
    custom_cat_res = await client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": "Coffee & Snacks", "type": "EXPENSE", "icon": "cafe", "color": "#7C3AED"},
    )
    assert custom_cat_res.status_code == 201
    custom_cat = custom_cat_res.json()
    assert custom_cat["name"] == "Coffee & Snacks"

    # 3. Create Account
    acc_res = await client.post(
        "/api/v1/accounts",
        headers=headers,
        json={"name": "HDFC Salary", "type": "BANK", "starting_balance": "50000.00"},
    )
    assert acc_res.status_code == 201
    acc = acc_res.json()
    assert acc["name"] == "HDFC Salary"
    assert acc["balance"] == "50000.00"

    # 4. List Accounts
    list_acc = await client.get("/api/v1/accounts", headers=headers)
    assert list_acc.status_code == 200
    assert len(list_acc.json()["items"]) == 1

    # 5. Update Account
    up_acc = await client.patch(
        f"/api/v1/accounts/{acc['id']}",
        headers=headers,
        json={"name": "HDFC Primary Account"},
    )
    assert up_acc.status_code == 200
    assert up_acc.json()["name"] == "HDFC Primary Account"
