import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_push_token_registration_and_deactivation(client: AsyncClient):
    # 1. Register user & login
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Notification Tester",
            "email": "push_test@example.com",
            "password": "SecretPassword123!",
            "confirm_password": "SecretPassword123!",
        },
    )
    assert reg_res.status_code == 201, reg_res.text

    login_res = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "push_test@example.com",
            "password": "SecretPassword123!",
        },
    )
    assert login_res.status_code == 200
    access_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 2. Register push token
    token_payload = {
        "push_token": "ExponentPushToken[AbCdEf123456SampleToken]",
        "device_type": "android",
    }
    reg_token_res = await client.post(
        "/api/v1/notifications/push-token",
        json=token_payload,
        headers=headers,
    )
    assert reg_token_res.status_code == 200, reg_token_res.text
    token_data = reg_token_res.json()
    assert token_data["push_token"] == "ExponentPushToken[AbCdEf123456SampleToken]"
    assert token_data["device_type"] == "android"
    assert token_data["is_active"] is True

    # 3. Deactivate push token
    unreg_res = await client.request(
        "DELETE",
        "/api/v1/notifications/push-token",
        json={"push_token": "ExponentPushToken[AbCdEf123456SampleToken]"},
        headers=headers,
    )
    assert unreg_res.status_code == 204
