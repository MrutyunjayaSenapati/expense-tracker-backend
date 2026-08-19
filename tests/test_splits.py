import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_multi_user_split_bill_flow(client: AsyncClient):
    # 1. Register and Login User A (Payer)
    res_a = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "usera@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "name": "User A",
        },
    )
    assert res_a.status_code == 201

    login_a = await client.post(
        "/api/v1/auth/login",
        json={"email": "usera@example.com", "password": "Password123!"},
    )
    assert login_a.status_code == 200
    token_a = login_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register and Login User B (Friend)
    res_b = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "userb@example.com",
            "password": "Password123!",
            "confirm_password": "Password123!",
            "name": "User B",
        },
    )
    assert res_b.status_code == 201

    login_b = await client.post(
        "/api/v1/auth/login",
        json={"email": "userb@example.com", "password": "Password123!"},
    )
    assert login_b.status_code == 200
    token_b = login_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. User A creates a split bill for Dinner (₹1,200 total; ₹400 User A, ₹400 User B, ₹400 Guest)
    create_res = await client.post(
        "/api/v1/splits",
        json={
            "title": "Team Dinner at Pizza Hut",
            "total_amount": 1200.0,
            "your_share": 400.0,
            "paid_by": "YOU",
            "participants": [
                {"name": "User B", "email_or_phone": "userb@example.com", "amount_owed": 400.0},
                {"name": "Guest Charlie", "email_or_phone": "+919876543210", "amount_owed": 400.0},
            ],
            "note": "Weekend dinner",
        },
        headers=headers_a,
    )
    assert create_res.status_code == 201
    bill_data = create_res.json()
    bill_id = bill_data["id"]
    assert bill_data["title"] == "Team Dinner at Pizza Hut"
    assert len(bill_data["participants"]) == 2

    # Find participant ID for User B
    user_b_participant = next(p for p in bill_data["participants"] if p["name"] == "User B")
    assert user_b_participant["is_paid"] is False

    # 4. User A checks summary (Should be owed ₹800)
    summary_a = await client.get("/api/v1/splits/summary", headers=headers_a)
    assert summary_a.status_code == 200
    assert float(summary_a.json()["total_owed_to_you"]) == 800.0
    assert float(summary_a.json()["total_you_owe"]) == 0.0

    # 5. User B logs in and checks /splits (Should see the bill synced!)
    list_b = await client.get("/api/v1/splits", headers=headers_b)
    assert list_b.status_code == 200
    assert len(list_b.json()) == 1
    assert list_b.json()[0]["id"] == bill_id

    # User B checks summary (Should owe ₹400)
    summary_b = await client.get("/api/v1/splits/summary", headers=headers_b)
    assert summary_b.status_code == 200
    assert float(summary_b.json()["total_you_owe"]) == 400.0
    assert float(summary_b.json()["total_owed_to_you"]) == 0.0

    # 6. User B settles their share
    settle_res = await client.patch(
        f"/api/v1/splits/{bill_id}/participants/{user_b_participant['id']}/settle",
        json={"is_paid": True},
        headers=headers_b,
    )
    assert settle_res.status_code == 200

    # 7. User A verifies that User B is now settled and total owed reduced to ₹400
    summary_a_after = await client.get("/api/v1/splits/summary", headers=headers_a)
    assert float(summary_a_after.json()["total_owed_to_you"]) == 400.0

    # 8. User A deletes the bill
    del_res = await client.delete(f"/api/v1/splits/{bill_id}", headers=headers_a)
    assert del_res.status_code == 204
