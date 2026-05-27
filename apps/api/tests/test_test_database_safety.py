import pytest

from conftest import require_test_database_url


def test_requires_test_database_url() -> None:
    with pytest.raises(RuntimeError, match="TEST_DATABASE_URL is required"):
        require_test_database_url("")


def test_refuses_database_url_that_does_not_look_like_test() -> None:
    with pytest.raises(RuntimeError, match="does not look like a test database"):
        require_test_database_url("postgresql+asyncpg://postgres:postgres@localhost:5432/elevator_commissioning")


def test_accepts_explicit_test_database_url() -> None:
    url = "postgresql+asyncpg://postgres:postgres@localhost:5432/elevator_commissioning_test"

    assert require_test_database_url(url) == url
