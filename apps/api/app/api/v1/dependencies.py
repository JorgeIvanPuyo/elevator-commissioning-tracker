from fastapi import HTTPException

from app.core.exceptions import AppError, ConflictError, NotFoundError


def to_http_exception(error: AppError) -> HTTPException:
    if isinstance(error, NotFoundError):
        return HTTPException(status_code=404, detail=error.message)
    if isinstance(error, ConflictError):
        return HTTPException(status_code=409, detail=error.message)
    return HTTPException(status_code=400, detail=error.message)
