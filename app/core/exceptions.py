from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        fields: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.fields = fields
        super().__init__(message)


class AuthenticationError(AppException):
    def __init__(self, message: str = "Invalid credentials", code: str = "AUTH_INVALID_CREDENTIALS"):
        super().__init__(code=code, message=message, status_code=status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(AppException):
    def __init__(self, message: str = "Forbidden", code: str = "FORBIDDEN"):
        super().__init__(code=code, message=message, status_code=status.HTTP_403_FORBIDDEN)


class ResourceNotFoundError(AppException):
    def __init__(self, message: str = "Resource not found", code: str = "NOT_FOUND"):
        super().__init__(code=code, message=message, status_code=status.HTTP_404_NOT_FOUND)


class ConflictError(AppException):
    def __init__(self, message: str = "Resource already exists", code: str = "CONFLICT"):
        super().__init__(code=code, message=message, status_code=status.HTTP_409_CONFLICT)


class ValidationAppError(AppException):
    def __init__(self, message: str = "Validation error", code: str = "VALIDATION_ERROR", fields: Optional[Dict[str, Any]] = None):
        status_code = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)
        super().__init__(code=code, message=message, status_code=status_code, fields=fields)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    content: Dict[str, Any] = {
        "error": {
            "code": exc.code,
            "message": exc.message,
        }
    }
    if exc.fields:
        content["error"]["fields"] = exc.fields
    return JSONResponse(status_code=exc.status_code, content=content)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    fields: Dict[str, str] = {}
    for err in exc.errors():
        loc = ".".join([str(l) for l in err["loc"] if l not in ("body", "query", "path")])
        fields[loc or "general"] = err["msg"]

    content = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Invalid request data",
            "fields": fields,
        }
    }
    status_code = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)
    return JSONResponse(status_code=status_code, content=content)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = "HTTP_ERROR"
    if exc.status_code == 401:
        code = "AUTH_UNAUTHORIZED"
    elif exc.status_code == 403:
        code = "FORBIDDEN"
    elif exc.status_code == 404:
        code = "NOT_FOUND"

    content = {
        "error": {
            "code": code,
            "message": exc.detail if isinstance(exc.detail, str) else "An error occurred",
        }
    }
    return JSONResponse(status_code=exc.status_code, content=content)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    content = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
        }
    }
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=content)
