import pytest
from httpx import AsyncClient


async def setup_user_and_account(client: AsyncClient, email: str = "fin_test@example.com"):
    await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Finance User",
            "email": email,
            "password": "Password123!",
            "confirm_password": "Password123!",
        },
    )
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create account with ₹10,000 starting balance
    acc_res = await client.post(
        "/api/v1/accounts",
        headers=headers,
        json={"name": "Wallet Cash", "type": "CASH", "starting_balance": "10000.00"},
    )
    account = acc_res.json()

    # Get a category
    cat_res = await client.get("/api/v1/categories?type=EXPENSE", headers=headers)
    category = cat_res.json()["items"][0]

    income_cat_res = await client.get("/api/v1/categories?type=INCOME", headers=headers)
    income_category = income_cat_res.json()["items"][0]

    return headers, account, category, income_category


@pytest.mark.asyncio
async def test_atomic_transaction_balance_lifecycle(client: AsyncClient):
    headers, account, category, income_category = await setup_user_and_account(client)
    account_id = account["id"]
    category_id = category["id"]

    # 1. Create Expense of ₹500
    txn_res = await client.post(
        "/api/v1/transactions",
        headers=headers,
        json={
            "account_id": account_id,
            "category_id": category_id,
            "amount": "500.00",
            "type": "EXPENSE",
            "merchant": "Swiggy Food",
            "note": "Dinner with friends",
        },
    )
    assert txn_res.status_code == 201, txn_res.text
    txn = txn_res.json()
    assert txn["amount"] == "500.00"

    # Verify account balance decreased by ₹500 to ₹9,500
    acc_check = await client.get(f"/api/v1/accounts/{account_id}", headers=headers)
    assert acc_check.json()["balance"] == "9500.00"

    # 2. Create Income of ₹2,000
    income_res = await client.post(
        "/api/v1/transactions",
        headers=headers,
        json={
            "account_id": account_id,
            "category_id": income_category["id"],
            "amount": "2000.00",
            "type": "INCOME",
            "merchant": "Client Bonus",
            "note": "Freelance project bonus",
        },
    )
    assert income_res.status_code == 201
    # Account balance should now be ₹11,500
    acc_check2 = await client.get(f"/api/v1/accounts/{account_id}", headers=headers)
    assert acc_check2.json()["balance"] == "11500.00"

    # 3. Update expense amount from ₹500 to ₹700
    up_res = await client.patch(
        f"/api/v1/transactions/{txn['id']}",
        headers=headers,
        json={"amount": "700.00"},
    )
    assert up_res.status_code == 200
    # Balance should adjust by -₹200 to ₹11,300
    acc_check3 = await client.get(f"/api/v1/accounts/{account_id}", headers=headers)
    assert acc_check3.json()["balance"] == "11300.00"

    # 4. Search and filtering
    search_res = await client.get(
        "/api/v1/transactions?search=friends",
        headers=headers,
    )
    assert search_res.status_code == 200
    items = search_res.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == txn["id"]

    # 5. Delete expense transaction -> Balance should increase back by ₹700 to ₹12,000
    del_res = await client.delete(f"/api/v1/transactions/{txn['id']}", headers=headers)
    assert del_res.status_code == 204

    acc_check4 = await client.get(f"/api/v1/accounts/{account_id}", headers=headers)
    assert acc_check4.json()["balance"] == "12000.00"
