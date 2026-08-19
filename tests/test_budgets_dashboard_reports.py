from datetime import date
import pytest
from httpx import AsyncClient
from tests.test_transactions_financial_integrity import setup_user_and_account


@pytest.mark.asyncio
async def test_budgets_dashboard_and_reports(client: AsyncClient):
    headers, account, category, income_category = await setup_user_and_account(
        client, "bdr_test@example.com"
    )
    account_id = account["id"]
    category_id = category["id"]

    today = date.today()
    start_date = date(today.year, today.month, 1)
    if today.month == 12:
        end_date = date(today.year + 1, 1, 1)
    else:
        end_date = date(today.year, today.month + 1, 1)

    # 1. Create a monthly budget of ₹10,000 with ₹5,000 for Food category
    budget_res = await client.post(
        "/api/v1/budgets",
        headers=headers,
        json={
            "name": "Current Month Budget",
            "amount": "10000.00",
            "period": "MONTHLY",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "categories": [{"category_id": category_id, "amount": "5000.00"}],
        },
    )
    assert budget_res.status_code == 201, budget_res.text
    budget = budget_res.json()
    assert budget["spent"] == "0.00"
    assert budget["status"] == "HEALTHY"

    # 2. Add an expense of ₹2,500
    await client.post(
        "/api/v1/transactions",
        headers=headers,
        json={
            "account_id": account_id,
            "category_id": category_id,
            "amount": "2500.00",
            "type": "EXPENSE",
            "merchant": "Supermarket",
        },
    )

    # 3. Check budget again -> spent should be ₹2,500, remaining ₹7,500, percentage 25.0%
    b_check = await client.get(f"/api/v1/budgets/{budget['id']}", headers=headers)
    assert b_check.status_code == 200
    b_data = b_check.json()
    assert b_data["spent"] == "2500.00"
    assert b_data["remaining"] == "7500.00"
    assert b_data["percentage_used"] == 25.0
    assert b_data["categories"][0]["spent"] == "2500.00"

    # 4. Check Dashboard
    dash_res = await client.get("/api/v1/dashboard", headers=headers)
    assert dash_res.status_code == 200
    dash = dash_res.json()
    assert dash["expenses"] == "2500.00"
    assert dash["budget"] is not None
    assert dash["budget"]["spent"] == "2500.00"
    assert len(dash["recent_transactions"]) >= 1

    # 5. Check Reports
    rep_res = await client.get("/api/v1/reports?period=week", headers=headers)
    assert rep_res.status_code == 200
    rep = rep_res.json()
    assert rep["expenses"] == "2500.00"
    assert len(rep["categories"]) >= 1
    assert rep["categories"][0]["amount"] == "2500.00"

    # 6. Check Gamification
    gam_res = await client.get("/api/v1/gamification", headers=headers)
    assert gam_res.status_code == 200
    gam = gam_res.json()
    assert gam["streak"]["current"] >= 1
    # FIRST_TRANSACTION achievement should be unlocked
    unlocked_codes = [a["code"] for a in gam["achievements"] if a["unlocked"]]
    assert "FIRST_TRANSACTION" in unlocked_codes

    # 7. Check CSV Export
    csv_res = await client.get("/api/v1/reports/export/csv", headers=headers)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers.get("content-type", "")
    assert "Supermarket" in csv_res.text
    assert "2500.00" in csv_res.text

