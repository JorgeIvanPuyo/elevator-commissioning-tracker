from dataclasses import dataclass


@dataclass(slots=True)
class AppError(Exception):
    message: str


class NotFoundError(AppError):
    pass


class ConflictError(AppError):
    pass
