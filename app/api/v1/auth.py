from typing import Optional
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.auth import (
    GoogleLoginRequest,
    LogoutRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterResponse,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    payload: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    user = await service.register(payload)
    return RegisterResponse(user=UserResponse.model_validate(user))


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and get tokens",
)
async def login(
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.login(payload)


@router.post(
    "/google",
    response_model=TokenResponse,
    summary="Authenticate with Google OAuth",
)
async def google_login(
    payload: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.google_login(payload)


@router.get(
    "/google/callback",
    summary="Google OAuth Callback Redirect Handler",
)
async def google_callback(
    request: Request,
    code: Optional[str] = None,
    id_token: Optional[str] = None,
    access_token: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    import traceback
    from fastapi.responses import HTMLResponse

    if error:
        return HTMLResponse(
            f"<div style='font-family:sans-serif;padding:20px;'><h3>Google Sign-In Error</h3><p>{error}</p></div>",
            status_code=400,
        )

    return_url = state or "expensetracker://oauth"
    tokens_query = ""

    # If code or id_token arrived in query params, attempt server-side verification
    if code or id_token or access_token:
        try:
            proto = request.headers.get("x-forwarded-proto", request.url.scheme)
            callback_uri = f"{proto}://{request.url.netloc}{request.url.path}"
            if "onrender.com" in callback_uri and callback_uri.startswith("http://"):
                callback_uri = callback_uri.replace("http://", "https://", 1)
            service = AuthService(db)
            req = GoogleLoginRequest(
                code=code,
                id_token=id_token,
                access_token=access_token,
                redirect_uri=callback_uri,
            )
            token_response = await service.google_login(req)
            tokens_query = (
                f"access_token={token_response.access_token}"
                f"&refresh_token={token_response.refresh_token}"
                f"&token_type=bearer"
                f"&expires_in={token_response.expires_in}"
            )
        except Exception as ex:
            print(f"⚠️ [Google Callback] Server-side verification fallback: {ex}")
            traceback.print_exc()

    if tokens_query:
        delimiter = "&" if ("?" in return_url or "#" in return_url) else "?"
        redirect_target = f"{return_url}{delimiter}{tokens_query}"
    elif code:
        delimiter = "&" if ("?" in return_url or "#" in return_url) else "?"
        redirect_target = f"{return_url}{delimiter}code={code}"
    else:
        redirect_target = return_url

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Signing in to Expense Tracker...</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: #0B0D14;
            color: #F8FAFC;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 20px;
        }}
        .card {{
            background: #141724;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            padding: 32px 24px;
            text-align: center;
            max-width: 400px;
            width: 100%;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
        }}
        .icon {{
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: rgba(99, 102, 241, 0.15);
            border: 1px solid rgba(99, 102, 241, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            font-size: 28px;
        }}
        h2 {{
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 8px;
            color: #FFFFFF;
        }}
        p {{
            color: #94A3B8;
            font-size: 14px;
            line-height: 1.5;
            margin-bottom: 24px;
        }}
        .btn {{
            display: block;
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
            color: #FFFFFF;
            text-decoration: none;
            font-weight: 600;
            font-size: 15px;
            border-radius: 12px;
            border: none;
            cursor: pointer;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
            transition: transform 0.1s ease;
        }}
        .btn:active {{
            transform: scale(0.98);
        }}
    </style>
</head>
<body>
    <div class="card">
        <div class="icon">✨</div>
        <h2>Signed In Successfully!</h2>
        <p>Returning you to the Expense Tracker app...</p>
        <a id="redirectBtn" class="btn" href="{redirect_target}">Open Expense Tracker 🚀</a>
    </div>

    <script>
        (function() {{
            const hash = window.location.hash.substring(1);
            let target = "{redirect_target}";
            
            if (hash) {{
                const urlParams = new URLSearchParams(window.location.search);
                const state = urlParams.get('state') || "{return_url}";
                target = state + (state.includes('?') ? '&' : '?') + hash;
            }}

            const btn = document.getElementById('redirectBtn');
            if (btn) {{
                btn.setAttribute('href', target);
            }}

            // Attempt instant automatic redirect
            try {{
                window.location.replace(target);
            }} catch (e) {{
                window.location.href = target;
            }}

            // Secondary auto-click after 300ms if browser needs DOM trigger
            setTimeout(function() {{
                if (btn) btn.click();
            }}, 300);
        }})();
    </script>
</body>
</html>"""
    return HTMLResponse(content=html)


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Refresh access token",
)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.refresh_token(payload.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke refresh token and log out",
)
async def logout(
    payload: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    await service.logout(payload.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user info",
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return UserResponse.model_validate(current_user)


@router.delete(
    "/account",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete account and user data",
)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    await service.delete_account(current_user.id)
