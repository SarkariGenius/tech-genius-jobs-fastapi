from fastapi import HTTPException, status
from typing import Any


class APIError(HTTPException):
    def __init__(self, code: str, message: str, status_code: int = 400, extra: dict[str, Any] | None = None):
        detail: dict[str, Any] = {"code": code, "message": message}
        if extra:
            detail.update(extra)
        super().__init__(status_code=status_code, detail=detail)
        self.code = code


def not_found(code: str, message: str) -> APIError:
    return APIError(code, message, status.HTTP_404_NOT_FOUND)


def bad_request(code: str, message: str) -> APIError:
    return APIError(code, message, status.HTTP_400_BAD_REQUEST)


def unauthorized(code: str, message: str) -> APIError:
    return APIError(code, message, status.HTTP_401_UNAUTHORIZED)


def forbidden(code: str, message: str) -> APIError:
    return APIError(code, message, status.HTTP_403_FORBIDDEN)


def conflict(code: str, message: str) -> APIError:
    return APIError(code, message, status.HTTP_409_CONFLICT)
