"""Describes the database that the integration tests run against."""

import re
from pathlib import Path
from typing import Final

_COMPOSE_FILE = Path(__file__).resolve().parents[4] / "ops" / "postgres.compose.yaml"

_IMAGE_LINE_PATTERN = re.compile(r"^\s+image:\s*(?P<image>\S+)\s*$", re.MULTILINE)

# The directory with the Alembic migration scripts.
MIGRATIONS_PATH = Path(__file__).resolve().parents[3] / "alembic"


def _read_postgres_image() -> str:
    images: Final = _IMAGE_LINE_PATTERN.findall(_COMPOSE_FILE.read_text(encoding="utf-8"))
    if len(images) != 1 or not images[0].startswith("postgres:"):
        message: Final = (
            f"Expected `{_COMPOSE_FILE}` to contain exactly one literal `postgres:` image, but found {images}."
        )
        raise RuntimeError(message)
    return images[0]


# The Docker image of the PostgreSQL server that the deployed database runs on.
POSTGRES_IMAGE = _read_postgres_image()
