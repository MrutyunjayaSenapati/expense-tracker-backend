import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login_flow(client: AsyncClient):
    # 1. Register
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Rahul Sharma",
            "email": "rahul@example.com",
            "password": "SecretPassword123!",
            "confirm_password": "SecretPassword123!",
        },
    )
    assert reg_res.status_code == 201, reg_res.text
    user_data = reg_res.json()["user"]
    assert user_data["email"] == "rahul@example.com"
    assert user_data["name"] == "Rahul Sharma"
    assert "id" in user_data

    # 2. Duplicate registration fails
    dup_res = await client.post(
        "/api/v1/auth/register",
        json={
            "name": "Rahul Dup",
            "email": "rahul@example.com",
            "password": "SecretPassword123!",
            "confirm_password": "SecretPassword123!",
        },
    )
    assert dup_res.status_code == 409
    assert dup_res.json()["error"]["code"] == "USER_ALREADY_EXISTS"

    # 3. Login
    login_res = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "rahul@example.com",
            "password": "SecretPassword123!",
        },
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert "refresh_token" in token_data
    assert token_data["token_type"] == "bearer"

    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]

    # 4. Get me
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "rahul@example.com"

    # 5. Refresh token
    ref_res = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert ref_res.status_code == 200
    new_access_token = ref_res.json()["access_token"]
    assert new_access_token

    # 6. Logout (revoke refresh token)
    logout_res = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {new_access_token}"},
        json={"refresh_token": refresh_token},
    )
    assert logout_res.status_code == 204

    # 7. Old refresh token should now fail
    ref_fail = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert ref_fail.status_code == 401
