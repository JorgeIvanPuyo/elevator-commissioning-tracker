import re

from app.core.exceptions import AppError

HEX_PATTERN = re.compile(r"^[0-9A-F]+$")


def normalize_hex_value(value: str | None) -> tuple[str | None, int | None]:
    if value is None:
        return None, None

    normalized = value.strip()
    if normalized == "":
        return None, None

    if normalized.lower().startswith("0x"):
        normalized = normalized[2:]

    normalized = normalized.upper()
    if not normalized or HEX_PATTERN.fullmatch(normalized) is None:
        raise AppError(f"Invalid HEX value: {value}")

    return normalized, int(normalized, 16)
