from decimal import Decimal
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_room_expenses_scenario(client: AsyncClient):
    # 1. Register and login User A, B, and C
    users = {}
    for name, email in [("User A", "user_a@room.com"), ("User B", "user_b@room.com"), ("User C", "user_c@room.com")]:
        reg_res = await client.post(
            "/api/v1/auth/register",
            json={
                "name": name,
                "email": email,
                "password": "Password123!",
                "confirm_password": "Password123!",
            },
        )
        assert reg_res.status_code == 201

        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "Password123!"},
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        users[name] = {
            "token": token,
            "headers": {"Authorization": f"Bearer {token}"},
            "id": reg_res.json()["user"]["id"],
        }

    # 2. User A creates group "Room Expenses" with members User B and User C
    create_group_res = await client.post(
        "/api/v1/groups",
        json={
            "name": "Room Expenses",
            "category": "HOME",
            "members": [
                {"name": "User B", "email_or_phone": "user_b@room.com"},
                {"name": "User C", "email_or_phone": "user_c@room.com"},
            ],
        },
        headers=users["User A"]["headers"],
    )
    assert create_group_res.status_code == 201
    group_data = create_group_res.json()
    group_id = group_data["id"]
    assert len(group_data["members"]) == 3

    member_a = next(m for m in group_data["members"] if m["name"] == "User A")
    member_b = next(m for m in group_data["members"] if m["name"] == "User B")
    member_c = next(m for m in group_data["members"] if m["name"] == "User C")

    # 3. User A logs Expense 1: ₹300 Groceries (paid by User A, split 3 ways)
    exp1_res = await client.post(
        f"/api/v1/groups/{group_id}/expenses",
        json={
            "title": "Groceries",
            "amount": 300.0,
            "paid_by_member_id": member_a["id"],
        },
        headers=users["User A"]["headers"],
    )
    assert exp1_res.status_code == 201

    # 4. User B logs Expense 2: ₹400 WiFi Bill (paid by User B, split 3 ways)
    exp2_res = await client.post(
        f"/api/v1/groups/{group_id}/expenses",
        json={
            "title": "WiFi Bill",
            "amount": 400.0,
            "paid_by_member_id": member_b["id"],
        },
        headers=users["User B"]["headers"],
    )
    assert exp2_res.status_code == 201
    dashboard_data = exp2_res.json()

    # 5. Verify Simplified Debts
    # Expected: User C owes User B ₹166.67 and owes User A ₹66.67
    debts = dashboard_data["simplified_debts"]
    assert len(debts) == 2

    debt_to_b = next(d for d in debts if d["to_member_name"] == "User B")
    assert debt_to_b["from_member_name"] == "User C"
    assert float(debt_to_b["amount"]) == 166.67

    debt_to_a = next(d for d in debts if d["to_member_name"] == "User A")
    assert debt_to_a["from_member_name"] == "User C"
    assert float(debt_to_a["amount"]) == 66.66

    # 6. User C settles ₹166.67 with User B
    settle1_res = await client.post(
        f"/api/v1/groups/{group_id}/settle",
        json={
            "from_user_id": users["User C"]["id"],
            "to_user_id": users["User B"]["id"],
            "amount": 166.67,
        },
        headers=users["User C"]["headers"],
    )
    assert settle1_res.status_code == 200
    assert len(settle1_res.json()["simplified_debts"]) == 1

    # 7. User C settles ₹66.66 with User A
    settle2_res = await client.post(
        f"/api/v1/groups/{group_id}/settle",
        json={
            "from_user_id": users["User C"]["id"],
            "to_user_id": users["User A"]["id"],
            "amount": 66.66,
        },
        headers=users["User C"]["headers"],
    )
    assert settle2_res.status_code == 200
    # Group is now 100% settled!
    assert len(settle2_res.json()["simplified_debts"]) == 0
