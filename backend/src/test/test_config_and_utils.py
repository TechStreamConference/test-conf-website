from datetime import UTC
from datetime import datetime
from typing import Final
from typing import final
from unittest.mock import Mock
from unittest.mock import call

import pytest
from pydantic import BaseModel

import backend.utils as utils_module
from backend.config import SETTINGS
from backend.models.responses import NotAuthenticatedResponseV1
from backend.utils import create_http_exception
from backend.utils import generate_browser_secret
from backend.utils import generate_session_token
from backend.utils import hash_token
from backend.utils import utc_now


@final
class _MultiFieldBody(BaseModel):
    detail: str
    reason: str


def test_settings_build_oidc_and_database_urls() -> None:
    assert SETTINGS.zitadel_redirect_uri == f"{SETTINGS.frontend_root_uri.rstrip('/')}/auth/callback"
    assert SETTINGS.async_database_url.startswith("postgresql+asyncpg://")
    assert SETTINGS.sync_database_url.startswith("postgresql+psycopg://")
    for url in (SETTINGS.async_database_url, SETTINGS.sync_database_url):
        assert SETTINGS.database_user in url
        assert SETTINGS.database_host in url
        assert str(SETTINGS.database_port) in url
        assert url.endswith(f"/{SETTINGS.database_name}")


def test_utc_now_returns_naive_utc_timestamp() -> None:
    before: Final = datetime.now(UTC).replace(tzinfo=None)
    result: Final = utc_now()
    after: Final = datetime.now(UTC).replace(tzinfo=None)

    assert result.tzinfo is None
    assert before <= result <= after


def test_secret_generators_use_expected_entropy(monkeypatch: pytest.MonkeyPatch) -> None:
    token_urlsafe: Final = Mock(side_effect=["browser", "session"])
    monkeypatch.setattr(utils_module.secrets, "token_urlsafe", token_urlsafe)

    assert generate_browser_secret() == "browser"
    assert generate_session_token() == "session"
    assert token_urlsafe.call_args_list == [
        call(32),
        call(32),
    ]


def test_hash_token_is_deterministic_sha256() -> None:
    assert hash_token("token") == "3c469e9d6c5875d37a43f353d4f88e61fcf812c66eee3457465a40b0da4153e0"
    assert hash_token("token") != hash_token("different")


def test_create_http_exception_unwraps_detail_only_model() -> None:
    exception: Final = create_http_exception(401, NotAuthenticatedResponseV1())

    assert exception.status_code == 401
    assert exception.detail == "Not authenticated."


def test_create_http_exception_preserves_multi_field_body() -> None:
    exception: Final = create_http_exception(400, _MultiFieldBody(detail="bad", reason="invalid"))

    assert exception.status_code == 400
    assert exception.detail == {"detail": "bad", "reason": "invalid"}
