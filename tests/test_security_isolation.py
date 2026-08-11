import pytest
from httpx import AsyncClient
from tests.test_transactions_financial_integrity import setup_user_and_account


@pytest.mark.asyncio
async def test_cross_user_isolation(client: AsyncClient):
    # Setup User A
    headers_a, acc_a, cat_a, _ = await setup_user_and_account(client, "user_a@example.com")
    # Setup User B
    headers_b, acc_b, cat_b, _ = await setup_user_and_account(client, "user_b@example.com")

    # User B creates a transaction
    txn_b_res = await client.post(
        "/api/v1/transactions",
        headers=headers_b,
        json={
            "account_id": acc_b["id"],
            "category_id": cat_b["id"],
            "amount": "999.00",
            "type": "EXPENSE",
            "merchant": "User B Secret Merchant",
        },
    )
    assert txn_b_res.status_code == 201
    txn_b_id = txn_b_res.json()["id"]

    # 1. User A tries to get User B's transaction -> 404 NOT_FOUND
    get_fail = await client.get(f"/api/v1/transactions/{txn_b_id}", headers=headers_a)
    assert get_fail.status_code == 404

    # 2. User A tries to update User B's transaction -> 404 NOT_FOUND
    up_fail = await client.patch(
        f"/api/v1/transactions/{txn_b_id}",
        headers=headers_a,
        json={"amount": "1.00"},
    )
    assert up_fail.status_code == 404

    # 3. User A tries to delete User B's transaction -> 404 NOT_FOUND
    del_fail = await client.delete(f"/api/v1/transactions/{txn_b_id}", headers=headers_a)
    assert del_fail.status_code == 404

    # 4. User A tries to access User B's account -> 404 NOT_FOUND
    acc_fail = await client.get(f"/api/v1/accounts/{acc_b['id']}", headers=headers_a)
    assert acc_fail.status_code == 404

    # 5. User A tries to create transaction on User B's account -> 422 VALIDATION_ERROR
    txn_hack = await client.post(
        "/api/v1/transactions",
        headers=headers_a,
        json={
            "account_id": acc_b["id"],
            "category_id": cat_a["id"],
            "amount": "50.00",
            "type": "EXPENSE",
        },
    )
    assert txn_hack.status_code == 422
